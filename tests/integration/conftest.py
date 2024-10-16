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

from os import path
import sys

sys.path += [path.join(path.dirname(__file__), "mender_integration")]

import logging

import pytest
from mender_integration.tests.conftest import unique_test_name
from mender_integration.tests.log import setup_test_logger

logging.getLogger("requests").setLevel(logging.CRITICAL)

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

collect_ignore = ["mender_integration"]


@pytest.fixture(scope="function", autouse=True)
def testlogger(request):
    test_name = unique_test_name(request)
    setup_test_logger(test_name)
    logging.getLogger().info("%s is starting.... " % test_name)
