# Copyright 2025 Northern.tech AS
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import os
import time
import pytest
import helpers
import logging

logger = logging.getLogger(__name__)

import definitions

from helpers import stdout
from device import NativeSim


class TestStateMachineTransitions:

    STATE_TO_CALLBACK = {
        "MENDER_UPDATE_STATE_DOWNLOAD": definitions.UM_DOWNLOAD_CALLBACK,
        "MENDER_UPDATE_STATE_INSTALL": definitions.UM_INSTALL_CALLBACK,
        "MENDER_UPDATE_STATE_REBOOT": definitions.UM_REBOOT_CALLBACK,
        "MENDER_UPDATE_STATE_VERIFY_REBOOT": definitions.UM_VERIFY_REBOOT_CALLBACK,
        "MENDER_UPDATE_STATE_COMMIT": definitions.UM_COMMIT_CALLBACK,
        "MENDER_UPDATE_STATE_ROLLBACK": definitions.UM_ROLLBACK_CALLBACK,
        "MENDER_UPDATE_STATE_ROLLBACK_REBOOT": definitions.UM_ROLLBACK_REBOOT_CALLBACK,
        "MENDER_UPDATE_STATE_ROLLBACK_VERIFY_REBOOT": definitions.UM_ROLLBACK_VERIFY_REBOOT_CALLBACK,
        "MENDER_UPDATE_STATE_FAILURE": definitions.UM_FAILURE_CALLBACK,
    }

    STATE_MACHINE_TEST_SET = {
        "success_no_reboot": {
            "Timeout": 120,
            "RequiresReboot": False,
            "SupportsRollback": False,
            "ExpectedSuccess": True,
            "ExpectedStateFlow": [
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_UPDATE_STATE_INSTALL",
                "MENDER_UPDATE_STATE_COMMIT",
                "MENDER_UPDATE_STATE_CLEANUP",
                "MENDER_UPDATE_STATE_END",
                "MENDER_CLIENT_STATE_OPERATIONAL",
            ],
        },
        "success_reboot": {
            "Timeout": 120,
            "RequiresReboot": True,
            "SupportsRollback": True,
            "ExpectedSuccess": True,
            "ExpectedStateFlow": [
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_UPDATE_STATE_INSTALL",
                "MENDER_UPDATE_STATE_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_COMMIT",
                "MENDER_UPDATE_STATE_CLEANUP",
                "MENDER_UPDATE_STATE_END",
                "MENDER_CLIENT_STATE_OPERATIONAL",
            ],
        },
        "fail_verify_reboot": {
            "Timeout": 120,
            "FailureInStates": ["MENDER_UPDATE_STATE_VERIFY_REBOOT"],
            "RequiresReboot": True,
            "SupportsRollback": True,
            "ExpectedSuccess": False,
            "ExpectedStateFlow": [
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_UPDATE_STATE_INSTALL",
                "MENDER_UPDATE_STATE_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_ROLLBACK",
                "MENDER_UPDATE_STATE_ROLLBACK_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_ROLLBACK_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_FAILURE",
                "MENDER_UPDATE_STATE_CLEANUP",
                "MENDER_UPDATE_STATE_END",
                "MENDER_CLIENT_STATE_OPERATIONAL",
            ],
        },
        "fail_commit": {
            "Timeout": 120,
            "FailureInStates": ["MENDER_UPDATE_STATE_COMMIT"],
            "RequiresReboot": True,
            "SupportsRollback": True,
            "ExpectedSuccess": False,
            "ExpectedStateFlow": [
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_UPDATE_STATE_INSTALL",
                "MENDER_UPDATE_STATE_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_COMMIT",
                "MENDER_UPDATE_STATE_ROLLBACK",
                "MENDER_UPDATE_STATE_ROLLBACK_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_ROLLBACK_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_FAILURE",
                "MENDER_UPDATE_STATE_CLEANUP",
                "MENDER_UPDATE_STATE_END",
                "MENDER_CLIENT_STATE_OPERATIONAL",
            ],
        },
        "fail_commit_no_rollback": {
            "Timeout": 120,
            "FailureInStates": ["MENDER_UPDATE_STATE_COMMIT"],
            "RequiresReboot": True,
            "SupportsRollback": False,
            "ExpectedSuccess": False,
            "ExpectedStateFlow": [
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_UPDATE_STATE_INSTALL",
                "MENDER_UPDATE_STATE_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_COMMIT",
                "MENDER_UPDATE_STATE_ROLLBACK",
                "MENDER_UPDATE_STATE_FAILURE",
                "MENDER_UPDATE_STATE_CLEANUP",
                "MENDER_UPDATE_STATE_END",
                "MENDER_CLIENT_STATE_OPERATIONAL",
            ],
        },
        "fail_download": {
            "Timeout": 120,
            "FailureInStates": ["MENDER_UPDATE_STATE_DOWNLOAD"],
            "RequiresReboot": True,
            "SupportsRollback": True,
            "ExpectedSuccess": False,
            "ExpectedStateFlow": [
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_UPDATE_STATE_CLEANUP",
                "MENDER_UPDATE_STATE_END",
                "MENDER_CLIENT_STATE_OPERATIONAL",
            ],
        },
        "fail_install": {
            "Timeout": 120,
            "FailureInStates": ["MENDER_UPDATE_STATE_INSTALL"],
            "RequiresReboot": True,
            "SupportsRollback": True,
            "ExpectedSuccess": False,
            "ExpectedStateFlow": [
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_UPDATE_STATE_INSTALL",
                "MENDER_UPDATE_STATE_FAILURE",
                "MENDER_UPDATE_STATE_CLEANUP",
                "MENDER_UPDATE_STATE_END",
                "MENDER_CLIENT_STATE_OPERATIONAL",
            ],
        },
        "fail_rollback_verify_reboot": {
            "Timeout": 120,
            "FailureInStates": [
                "MENDER_UPDATE_STATE_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_ROLLBACK_VERIFY_REBOOT",
            ],
            "RequiresReboot": True,
            "SupportsRollback": True,
            "ExpectedSuccess": False,
            "ExpectedStateFlow": [
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_UPDATE_STATE_INSTALL",
                "MENDER_UPDATE_STATE_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_ROLLBACK",
                "MENDER_UPDATE_STATE_ROLLBACK_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_ROLLBACK_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_ROLLBACK_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_ROLLBACK_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_ROLLBACK_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_ROLLBACK_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_ROLLBACK_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_ROLLBACK_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_ROLLBACK_REBOOT",
                "MENDER_UPDATE_STATE_CLEANUP",
                "MENDER_UPDATE_STATE_END",
                "MENDER_CLIENT_STATE_OPERATIONAL",
            ],
        },
        "fail_commit_rollback": {
            "Timeout": 120,
            "FailureInStates": [
                "MENDER_UPDATE_STATE_COMMIT",
                "MENDER_UPDATE_STATE_ROLLBACK",
            ],
            "RequiresReboot": True,
            "SupportsRollback": True,
            "ExpectedSuccess": False,
            "ExpectedStateFlow": [
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_UPDATE_STATE_INSTALL",
                "MENDER_UPDATE_STATE_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_COMMIT",
                "MENDER_UPDATE_STATE_ROLLBACK",
                "MENDER_UPDATE_STATE_FAILURE",
                "MENDER_UPDATE_STATE_CLEANUP",
                "MENDER_UPDATE_STATE_END",
                "MENDER_CLIENT_STATE_OPERATIONAL",
            ],
        },
        "noop_check_deployment": {
            "Timeout": 45,
            "RequiresReboot": False,
            "SupportsRollback": False,
            "ExpectedStateFlow": [
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_CLIENT_STATE_OPERATIONAL",
            ],
        },
    }

    SPONTANEOUS_REBOOT_TEST_SET = {
        "spontaneous_reboot_install": {
            "Timeout": 120,
            "RebootInState": "MENDER_UPDATE_STATE_INSTALL",
            "RequiresReboot": True,
            "SupportsRollback": True,
            "ExpectedSuccess": False,
            "ExpectedStateFlow": [
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_UPDATE_STATE_INSTALL",  # reboot
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_INSTALL",
                "MENDER_UPDATE_STATE_FAILURE",
                "MENDER_UPDATE_STATE_CLEANUP",
                "MENDER_UPDATE_STATE_END",
                "MENDER_CLIENT_STATE_OPERATIONAL",
            ],
        },
        "spontaneous_reboot_commit": {
            "Timeout": 120,
            "RebootInState": "MENDER_UPDATE_STATE_COMMIT",
            "RequiresReboot": True,
            "SupportsRollback": True,
            "ExpectedSuccess": False,
            "ExpectedStateFlow": [
                "MENDER_CLIENT_STATE_OPERATIONAL",
                "MENDER_UPDATE_STATE_DOWNLOAD",
                "MENDER_UPDATE_STATE_INSTALL",
                "MENDER_UPDATE_STATE_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_COMMIT",  # reboot
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_COMMIT",
                "MENDER_UPDATE_STATE_ROLLBACK",
                "MENDER_UPDATE_STATE_ROLLBACK_REBOOT",
                "MENDER_CLIENT_STATE_PENDING_REBOOT",
                "MENDER_CLIENT_STATE_INITIALIZATION",
                "MENDER_UPDATE_STATE_ROLLBACK_VERIFY_REBOOT",
                "MENDER_UPDATE_STATE_FAILURE",
                "MENDER_UPDATE_STATE_CLEANUP",
                "MENDER_UPDATE_STATE_END",
                "MENDER_CLIENT_STATE_OPERATIONAL",
            ],
        },
    }

    FAILED_DEPLOYMENT = "deployment_status_cb: failure"
    SUCCESSFUL_DEPLOYMENT = "deployment_status_cb: success"

    def do_test(self, server, get_build_dir, test_state_set, state_set_key):
        device = NativeSim(get_build_dir, stdout=True)

        state_set = test_state_set[state_set_key]
        successful_test = False
        traversed_states = []

        for state in state_set.get("FailureInStates", []):
            macro = r"""
            return MENDER_FAIL; \
            """
            helpers.set_callback(self.STATE_TO_CALLBACK[state], macro)

        if state_set["RequiresReboot"]:
            helpers.set_define(definitions.UM_REQUIRES_REBOOT, "true")
        if state_set["SupportsRollback"]:
            helpers.set_define(definitions.UM_SUPPORTS_ROLLBACK, "true")

        is_noop = state_set_key == "noop_check_deployment"

        try:
            # Set host and tenant in the device
            device.set_host(f"https://{server.host}")
            device.set_tenant(server.get_tenant_token())

            # Start device
            extra_variables = [
                "-DCONFIG_MENDER_HEAP_SIZE=12",
                "-DCONFIG_MENDER_MAX_STATE_DATA_STORE_COUNT=12",
                "-DCONFIG_LOG_BACKEND_SHOW_COLOR=n",
            ]
            device.start(pristine=True, extra_variables=extra_variables)

            server.accept_device()
            device.status.is_authenticated(timeout=60)
            artifact_name = server.upload_artifact(
                "test-mender-mcu-state-machine", device_types=("native_sim/native",)
            )

            active_deployment = False
            state_machine_done = False
            had_spontaneous_reboot = False

            start_time = time.time()
            while time.time() - start_time < state_set["Timeout"]:
                line = stdout(device)

                # The noop tests checks for deployment -> operational
                if (
                    is_noop
                    and traversed_states.count("MENDER_UPDATE_STATE_DOWNLOAD") == 2
                ):
                    state_machine_done = True

                if not active_deployment and not is_noop:
                    # We have to ensure that we are capturing stdout
                    # before creating the deploymet to ensure that we
                    # catch the first state
                    server.create_deployment(artifact_name, server.device_id, True)
                    active_deployment = True

                if (
                    self.FAILED_DEPLOYMENT in line and not state_set["ExpectedSuccess"]
                ) or (
                    self.SUCCESSFUL_DEPLOYMENT in line and state_set["ExpectedSuccess"]
                ):
                    successful_test = True

                elif "Waiting for a reboot" in line:
                    device.restart()

                elif "Entering state" in line or "Resuming from state" in line:
                    state = line.split()[-1]
                    assert state
                    if (
                        state_set.get("RebootInState") == state
                        and not had_spontaneous_reboot
                    ):
                        device.restart()
                        had_spontaneous_reboot = True
                    traversed_states.append(state)
                    if "MENDER_UPDATE_STATE_END" == state:
                        state_machine_done = True

                # Check that the client is operational after
                # the state machine is done
                elif "Inside work function" in line:
                    client_state = line.split()[-1][:-1]
                    traversed_states.append(client_state)
                    if (
                        state_machine_done
                        and "MENDER_CLIENT_STATE_OPERATIONAL" == client_state
                    ):
                        break

            assert (
                traversed_states == state_set["ExpectedStateFlow"]
            ), f"Actual states: {traversed_states}\nExpected flow: {state_set['ExpectedStateFlow']}"
            # Validate deployment status
            if not successful_test and not is_noop:
                status = "success" if state_set["ExpectedSuccess"] else "failure"
                pytest.fail(f"Expected deployment status to be a {status}")

        finally:
            # abort to ensure deployment is over after test
            server.abort_deployment()
            device.stop()

    @pytest.mark.parametrize("state_set", STATE_MACHINE_TEST_SET.keys())
    def test_state_machine(self, server, get_build_dir, state_set):
        self.do_test(server, get_build_dir, self.STATE_MACHINE_TEST_SET, state_set)

    @pytest.mark.parametrize("state_set", SPONTANEOUS_REBOOT_TEST_SET.keys())
    def test_spontaneous_reboot(self, server, get_build_dir, state_set):
        self.do_test(server, get_build_dir, self.SPONTANEOUS_REBOOT_TEST_SET, state_set)
