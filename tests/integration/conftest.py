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
import sys
import logging
import tempfile
import subprocess
import pytest

from helpers import THIS_DIR

from os import path
from pathlib import Path

sys.path += [path.join(path.dirname(__file__), "mender_server/")]
sys.path += [
    path.join(path.dirname(__file__), "mender_server/backend/tests/integration/")
]

from server import Server

logging.getLogger("requests").setLevel(logging.CRITICAL)

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

collect_ignore = ["mender_server"]

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function", autouse=True)
def testlogger(request):
    logging.getLogger().info("%s is starting.... " % __name__)


def pytest_addoption(parser):
    parser.addoption(
        "--host",
        action="store",
        default="docker.mender.io",
        help="Server URL for tests",
    )


@pytest.fixture(scope="session", autouse=True)
def setup_user():
    # for now this just returns auth token from env
    # but for demo server, it should create a user aswell
    return os.getenv("TEST_AUTH_TOKEN")


@pytest.fixture(scope="session", autouse=True)
def server(setup_user, request):
    host_url = request.config.getoption("--host")
    return Server(auth_token=setup_user, host=host_url)


@pytest.fixture(scope="function", autouse=True)
def get_build_dir():
    return tempfile.mkdtemp()


@pytest.fixture(scope="function", autouse=True)
def get_coverage(request, get_build_dir):
    yield
    test_name = request.node.name
    command = [
        "lcov",
        "--capture",
        "--directory",
        path.join(get_build_dir, "modules/mender-mcu"),
        "--output-file",
        path.join(THIS_DIR, f"{test_name}.info"),
        "--rc",
        "lcov_branch_coverage=1",
    ]
    exclude = ["--exclude", "*/modules/crypto/*", "--exclude", "*/zephyr/include/*"]
    command.extend(exclude)

    logger.info(f"Generating coverage for {test_name}")
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as err:
        pytest.fail(err.stderr)


@pytest.fixture(scope="session", autouse=True)
def aggregate_coverage():
    yield
    covfiles = Path(THIS_DIR).rglob("test*.info")
    files = [file for file in covfiles if file.is_file()]
    command = ["lcov"]
    for file in files:
        command.extend(["--add-tracefile", str(file)])
    command.extend(["-o", "coverage.lcov"])

    logger.info("Aggregating coverage reports")
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as err:
        pytest.fail(err.stderr)

    for file in files:
        if path.exists(file):
            os.remove(file)
        else:
            pytest.fail()
