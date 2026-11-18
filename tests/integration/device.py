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
import glob
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


def sanitizer_log_prefix(build_dir):
    return os.path.join(build_dir, "asan")


def sanitizer_reports(build_dir):
    """Return the contents of all sanitizer reports written by devices built
    in build_dir, an empty list if there are none"""
    reports = []
    for report in sorted(glob.glob(sanitizer_log_prefix(build_dir) + ".*")):
        with open(report, "r", errors="replace") as f:
            reports.append(f.read())
    return reports


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
    # Build with AddressSanitizer (incl. LeakSanitizer). Set globally from the
    # --sanitize pytest option, see conftest.py
    sanitize = False

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
            f'-DCONFIG_MENDER_SERVER_TENANT_TOKEN="{self.server_tenant}"',
        ] + extra_variables
        if self.sanitize:
            variables += ["-DCONFIG_ASAN=y"]
        if self.mac_address:
            variables += [
                "-DCONFIG_ETH_NATIVE_TAP_RANDOM_MAC=n",
               f'-DCONFIG_ETH_NATIVE_TAP_MAC_ADDR="{self.mac_address}"',
            ]

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

        command = [
            f"{self.build_dir}/zephyr/zephyr.exe",
            f"--flash={self.build_dir}/flash.bin",
        ]
        if self._log_stdout:
            self._output_file = f"{self.build_dir}/{os.getpid()}_{time.time_ns()}.out"
            proc_output = open(self._output_file, "w")
            self.output = open(self._output_file, "r")
            self.proc = subprocess.Popen(
                command,
                stdout=proc_output,
                stderr=subprocess.STDOUT,
                text=True,
                env=self._env(),
            )
        else:
            self.proc = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=self._env(),
            )
        logger.info("Started device")

    def _env(self):
        if not self.sanitize:
            return None
        env = dict(os.environ)
        # Reports go to <build_dir>/asan.<pid> (one file per process, so also
        # across reboots) and are collected by the check_sanitizers fixture.
        # Any ASAN_OPTIONS already in the environment are appended so they
        # take precedence, which is handy when debugging locally.
        options = [
            f"log_path={sanitizer_log_prefix(self.build_dir)}",
            "halt_on_error=1",
            "detect_leaks=1",
        ]
        if env.get("ASAN_OPTIONS"):
            options.append(env["ASAN_OPTIONS"])
        env["ASAN_OPTIONS"] = ":".join(options)
        return env

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
