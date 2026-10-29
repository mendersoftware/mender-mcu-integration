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
import random
import string
import tempfile
import time
import pytest
import subprocess

from os import path
from contextlib import contextmanager

import logging

logger = logging.getLogger(__name__)


THIS_DIR = path.dirname(os.path.abspath(__file__))


def get_header_file():
    return path.join(THIS_DIR, "src/test_definitions.h")


def create_header_file():
    if not path.exists(get_header_file()):
        open(get_header_file(), "w").close()


# The name of the configurable callbacks can be found in definition.py
def set_callback(function_name, definition):
    with open(get_header_file(), "a") as f:
        f.write(f"#define {function_name}() \\{definition}\n")


# The name of the configurable variables can be found in definitions.py
def set_define(define_name, definition):
    with open(get_header_file(), "a") as f:
        f.write(f"#define {define_name} {definition}\n")


def stdout(device):
    if device.output is None:
        raise ValueError("Device has no output")

    while True:
        line = device.output.readline()
        if line:
            return line
        if not device.is_running():
            return device.output.read()
        else:
            time.sleep(0.1)


def read_log(device, until, timeout=60):
    """Read device output until a line containing `until` shows up and return all
    lines read so far. Fails the test on timeout or if the device exits first."""
    lines = []
    start_time = time.time()
    while time.time() - start_time < timeout:
        line = stdout(device)
        lines.append(line)
        if until in line:
            return lines
        if not device.is_running():
            break
    logger.debug("=== Device logs follow ===\n" + "".join(lines))
    pytest.fail(f"'{until}' not found in device output")


def log_contains(lines, text):
    return any(text in line for line in lines)


def boot(device, until, timeout=60):
    """Start the (already compiled) device, read its output until a line
    containing `until` shows up, stop it and return the lines read"""
    device.start(compile=False)
    try:
        return read_log(device, until, timeout)
    finally:
        device.stop()


# get_mender_artifact from testutils/common.py didn't support uncompressed artifacts
@contextmanager
def get_uncompressed_mender_artifact(
    artifact_name="test",
    update_module="dummy",
    device_types=("arm1",),
    size=256,
    depends=(),
    provides=(),
):
    data = "".join(random.choices(string.ascii_uppercase + string.digits, k=size))
    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(data.encode("utf-8"))
    f.close()
    #
    filename = f.name
    artifact = "%s.mender" % filename
    args = [
        "mender-artifact",
        "write",
        "module-image",
        "-o",
        artifact,
        "--artifact-name",
        artifact_name,
        "-T",
        update_module,
        "-f",
        filename,
        "--compression",
        "none",
    ]

    for device_type in device_types:
        args.extend(["-t", device_type])
    for depend in depends:
        args.extend(["--depends", depend])
    for provide in provides:
        args.extend(["--provides", provide])
    try:
        subprocess.call(args)
        yield artifact
    finally:
        os.unlink(filename)
        os.path.exists(artifact) and os.unlink(artifact)
