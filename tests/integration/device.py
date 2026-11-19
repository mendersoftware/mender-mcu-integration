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
import queue
import threading

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
                return
        pytest.fail("Failed to authenticate device")

    def is_aborted(self, timeout=60):
        start_time = time.time()
        while time.time() - start_time < timeout:
            logger.info("Waiting for deployment to abort")
            line = stdout(self.device)
            if "Deployment aborted" in line:
                return True
        return False


class NativeSim:
    def __init__(self, build_dir, log_stdout=True):
        self.tenant_token = "..."
        self.proc = None
        self._log_stdout = log_stdout
        self._output_file = None
        self.output = None

        self.server_host = ""
        self.server_tenant = ""
        self.mac_address = ""

        self.status = DeviceStatus(self)

        # Defaults to `https://docker.mender.io`
        self.set_host()

        create_header_file()

        self.build_dir = build_dir

    def set_host(self, host="https://docker.mender.io"):
        self.server_host = host

    def set_tenant(self, tenant):
        self.server_tenant = tenant

    def set_mac(self, mac_address):
        self.mac_address = mac_address

    def compile(self, pristine=False, extra_variables=None):
        if self.server_host == "https://hosted.mender.io":
            extra_host_arg = "-DCONFIG_MENDER_SERVER_HOST_US=y"
        elif self.server_host == "https://eu.hosted.mender.io":
            extra_host_arg = "-DCONFIG_MENDER_SERVER_HOST_EU=y"
        else:
            extra_host_arg = "-DCONFIG_MENDER_SERVER_HOST_ON_PREM=y"

        if extra_variables is None:
            extra_variables = []

        variables = [
            "-DCONFIG_COVERAGE=y",
            "-DBUILD_INTEGRATION_TESTS=ON",
            f'-DCONFIG_MENDER_SERVER_HOST="{self.server_host}"', extra_host_arg,
        ] + extra_variables
        if self.mac_address:
            variables += [
                "-DCONFIG_ETH_NATIVE_TAP_RANDOM_MAC=n",
               f'-DCONFIG_ETH_NATIVE_TAP_MAC_ADDR="{self.mac_address}"',
            ]

        # Pass the tenant token through a Kconfig fragment file instead of on
        # the command line. west/cmake echo the build command to stderr (and
        # pytest prints it in tracebacks) on failure, so a token passed as a
        # -D argument would leak into the logs despite stdout being silenced.
        # Only the file path appears in any echoed command.
        tenant_token_conf = tempfile.NamedTemporaryFile(
            mode="w", suffix=".conf", delete=False
        )
        try:
            tenant_token_conf.write(
                f'CONFIG_MENDER_SERVER_TENANT_TOKEN="{self.server_tenant}"\n'
            )
            tenant_token_conf.close()

            extra_conf_files = ";".join(
                [
                    os.path.join(THIS_DIR, "integration_tests.conf"),
                    tenant_token_conf.name,
                ]
            )
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
                    "-DEXTRA_CONF_FILE=" + extra_conf_files,
                ]
                + variables
            )

            try:
                # Don't log stdout - as it may contain the tenant token
                subprocess.check_call(command, stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError as result:
                logger.error(result.stderr)
                command_output = " ".join(command)
                pytest.fail(f"Failed to compile with command: {command_output}")
        finally:
            os.unlink(tenant_token_conf.name)

    def start(self, compile=True, pristine=False, extra_variables=None):
        if extra_variables is None:
            extra_variables = []
        if compile:
            self.compile(pristine=pristine, extra_variables=extra_variables)

        if self._log_stdout:
            self._output_file = f"{self.build_dir}/{os.getpid()}_{time.time_ns()}.out"
            proc_output = open(self._output_file, "w")
            self.output = open(self._output_file, "r")
            self.proc = subprocess.Popen(
                [
                    f"{self.build_dir}/zephyr/zephyr.exe",
                    f"--flash={self.build_dir}/flash.bin",
                ],
                stdout=proc_output,
                stderr=subprocess.STDOUT,
                text=True,
            )
        else:
            self.proc = subprocess.Popen(
                [
                    f"{self.build_dir}/zephyr/zephyr.exe",
                    f"--flash={self.build_dir}/flash.bin",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        logger.info("Started device")

    def is_running(self):
        if not self.proc:
            return False
        try:
            os.kill(self.proc.pid, 0)
            return True
        except:
            return False

    def stop(self, stop_after=0):
        if self.proc is None:
            return
        time.sleep(stop_after)
        self.proc.terminate()
        self.proc.wait()
        logger.info("Stopped device")

    def restart(self):
        self.stop()
        self.start(compile=False)

    def clean_build(self):
        shutil.rmtree(self.build_dir)

    def get_output(self):
        with open(self._output_file, "r") as f:
            return f.read()
