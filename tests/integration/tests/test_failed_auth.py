# Copyright 2026 Northern.tech AS
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

import time
import logging

import helpers
import definitions
from helpers import stdout

logger = logging.getLogger(__name__)

FAILED_DEPLOYMENT = "deployment_status_cb: failure"
SUCCESSFUL_DEPLOYMENT = "deployment_status_cb: success"
AUTH_FAILED_BEFORE_COMMIT = "Failed to authenticate before commit, rejecting the update"
COMMIT_CALLBACK_CALLED = "UM commit callback called"


class TestFailedAuthentication:
    """Tests for the different ways device authentication can fail, both
    outside of and during a deployment."""

    # --- Failures during a deployment ---

    def test_reboot_failed_auth(self, server, device, mac_address):
        """During a deployment reboot the device, a failed authentication
        (device rejected/decommissioned while rebooting) results in a failed
        deployment and rollback. Relies on CONFIG_MENDER_COMMIT_REQUIRE_AUTH,
        where the client drops its token and re-authenticates before COMMIT."""
        expected_states = [
            "MENDER_UPDATE_STATE_DOWNLOAD",
            "MENDER_UPDATE_STATE_INSTALL",
            "MENDER_UPDATE_STATE_REBOOT",
            "MENDER_UPDATE_STATE_VERIFY_REBOOT",
            "MENDER_UPDATE_STATE_COMMIT",
            "MENDER_UPDATE_STATE_ROLLBACK",
            "MENDER_UPDATE_STATE_ROLLBACK_REBOOT",
            "MENDER_UPDATE_STATE_ROLLBACK_VERIFY_REBOOT",
            "MENDER_UPDATE_STATE_FAILURE",
            "MENDER_UPDATE_STATE_CLEANUP",
            "MENDER_UPDATE_STATE_END",
        ]

        helpers.set_define(definitions.UM_REQUIRES_REBOOT, "true")
        helpers.set_define(definitions.UM_SUPPORTS_ROLLBACK, "true")
        helpers.set_callback(
            definitions.UM_COMMIT_CALLBACK,
            "\n" + r'printf("%s\n");' % COMMIT_CALLBACK_CALLED,
        )

        try:
            device.start(
                pristine=True,
                extra_variables=[
                    "-DCONFIG_MENDER_COMMIT_REQUIRE_AUTH=y",
                    "-DCONFIG_MENDER_HEAP_SIZE=12",
                    "-DCONFIG_MENDER_MAX_STATE_DATA_STORE_COUNT=12",
                    "-DCONFIG_LOG_BACKEND_SHOW_COLOR=n",
                ],
            )
            server.accept_device(mac_address)
            device.status.is_authenticated(timeout=60)

            artifact_name = server.upload_artifact(
                "test-failed-auth-reboot", device_types=("test-device",)
            )
            server.create_deployment(artifact_name, server.device_id, True)

            traversed_states = []
            lines = []
            rejected = False
            start_time = time.time()
            while time.time() - start_time < 180:
                line = stdout(device)
                lines.append(line)

                if "Waiting for a reboot" in line:
                    if not rejected:
                        # Make authentication fail once the device is back up
                        device.stop()
                        server.reject_device()
                        rejected = True
                        device.start(compile=False)
                    else:
                        # Rollback reboot
                        device.restart()

                elif "Entering state" in line or "Resuming from state" in line:
                    state = line.split()[-1]
                    traversed_states.append(state)
                    if state == "MENDER_UPDATE_STATE_END":
                        break

            output = "".join(lines)
            logger.debug("=== Device logs follow ===\n" + output)

            assert rejected, "Device never got to the update reboot"
            assert (
                traversed_states == expected_states
            ), f"Actual states: {traversed_states}\nExpected flow: {expected_states}"
            assert AUTH_FAILED_BEFORE_COMMIT in output
            assert COMMIT_CALLBACK_CALLED not in output
            assert FAILED_DEPLOYMENT in output
            assert SUCCESSFUL_DEPLOYMENT not in output
        finally:
            server.abort_deployment()
