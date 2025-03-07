# Copyright 2024 Northern.tech AS
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
import shutil
import tempfile
import subprocess
import logging

logger = logging.getLogger(__name__)

from helpers import stdout
from helpers import create_header_file
from helpers import THIS_DIR

# This has to point the west workspace containing mender-mcu-integration
WORKSPACE_DIRECTORY = os.path.join(THIS_DIR, "../../")


class DeviceStatus:
    def __init__(self, device):
        self.device = device

    def is_authenticated(self, timeout=60):
        logger.info("Waiting for device to authenticate")
        start_time = time.time()
        while time.time() - start_time < timeout:
            line = stdout(self.device)
            if "Authenticated successfully" in line:
                logger.info("Device authenticated")
                return True
        return False

    def is_aborted(self, timeout=60):
        start_time = time.time()
        while time.time() - start_time < timeout:
            logger.info("Waiting for deployment to abort")
            line = stdout(self.device)
            if "Deployment aborted" in line:
                return True
        return False


class NativeSim:
    def __init__(self, build_dir, stdout=False):
        self.tenant_token = "..."
        self.proc = None
        self.stdout = stdout

        self.server_host = ""
        self.server_tenant = ""

        self.status = DeviceStatus(self)

        # Defaults to `https://docker.mender.io`
        self.set_host()

        create_header_file()

        self.build_dir = build_dir

    def set_host(self, host="https://docker.mender.io"):
        self.server_host = host

    def set_tenant(self, tenant):
        self.server_tenant = tenant

    def compile(self, pristine=False, extra_variables=None):
        if extra_variables is None:
            extra_variables = []
        if compile:
            variables = [
                "-DCONFIG_COVERAGE=y",
                "-DBUILD_INTEGRATION_TESTS=ON",
                f'-DCONFIG_MENDER_SERVER_HOST="{self.server_host}"',
                f'-DCONFIG_MENDER_SERVER_TENANT_TOKEN="{self.server_tenant}"',
            ] + extra_variables

            command = (
                [
                    "west",
                    "build",
                    "--board",
                    "native_sim",
                    WORKSPACE_DIRECTORY,
                    "--build-dir",
                    f"{self.build_dir}",
                ]
                + (["--pristine"] if pristine else [])
                + [
                    "--",
                    "-DEXTRA_CONF_FILE="
                    + f"{os.path.join(THIS_DIR, 'integration_tests.conf')}",
                ]
                + variables
            )

            try:
                # Don't log stdout - as it contains the tenant token
                subprocess.check_call(command, stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError as result:
                logger.error(result.stderr)
                command_output = " ".join(command)
                pytest.fail(f"Failed to compile with command: {command_output}")

    def start(self, compile=True, pristine=False, extra_variables=None):
        if extra_variables is None:
            extra_variables = []
        if compile:
            self.compile(pristine=pristine, extra_variables=extra_variables)

        self.proc = subprocess.Popen(
            [
                f"{self.build_dir}/zephyr/zephyr.exe",
                f"--flash={self.build_dir}/flash.bin",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.info("Started device")

    def stop(self, stop_after=0):
        time.sleep(stop_after)
        self.proc.terminate()
        self.proc.wait()
        logger.info("Stopped device")

    def restart(self):
        self.stop()
        self.start(compile=False)

    def clean_build(self):
        shutil.rmtree(self.build_dir)
