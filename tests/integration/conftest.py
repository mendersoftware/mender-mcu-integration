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
from os import path

import sys
import logging
import pytest

sys.path += [path.join(path.dirname(__file__), "mender_integration")]
sys.path += [
    path.join(path.dirname(__file__), "mender_server/backend/tests/integration/tests/")
]

from server import Server

from mender_integration.tests.conftest import unique_test_name
from mender_integration.tests.log import setup_test_logger

logging.getLogger("requests").setLevel(logging.CRITICAL)

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

collect_ignore = ["mender_integration", "mender_server"]


@pytest.fixture(scope="function", autouse=True)
def testlogger(request):
    test_name = unique_test_name(request)
    setup_test_logger(test_name)
    logging.getLogger().info("%s is starting.... " % test_name)


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
