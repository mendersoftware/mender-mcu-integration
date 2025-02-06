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
import helpers
import logging

logger = logging.getLogger(__name__)

from helpers import stdout
from device import NativeSim

import definitions


@pytest.fixture
def teardown():
    yield
    if os.path.exists(helpers.get_header_file()):
        os.remove(helpers.get_header_file())


@pytest.fixture(scope="session")
def check_variables():
    missing_vars = []
    for var in ("TEST_DEVICE_ID", "TEST_TENANT_TOKEN", "TEST_AUTH_TOKEN"):
        if var not in os.environ:
            missing_vars.append(var)
    if missing_vars:
        pytest.fail(f"Failed to set {', '.join(missing_vars)}")


def test_deployment_abort(teardown, server, check_variables):

    """
    Sample test to demonstrate use of framework
    """

    # Temporary workaround for the PoC
    device_id = os.getenv("TEST_DEVICE_ID")
    artifact_name = server.upload_artifact(
        "test-artifact", device_types=("native_sim/native",)
    )

    download_body = r"""
    static int counter = 0; \
    if (counter == 0) { \
        printf("Sleeping in download\n"); \
        k_sleep(K_SECONDS(5)); \
    }\
    counter++; \
    """
    helpers.set_callback(definitions.UM_DOWNLOAD_CALLBACK, download_body)

    device = NativeSim(stdout=True)
    # Set host and tenant in the device
    device.set_host("https://hosted.mender.io")

    # Temporary workaround for the PoC
    device.set_tenant(os.getenv("TEST_TENANT_TOKEN"))

    # Start device
    device.start(pristine=True)
    device.status.is_authenticated(timeout=60)

    # Create deployment
    server.create_deployment(artifact_name, device_id, True)

    # Wait for download callback to sleep so we can abort
    timeout = 60
    start_time = time.time()
    while time.time() - start_time < timeout:
        line = stdout(device)
        if "Sleeping in download\n" in line:
            server.abort_deployment()
            break

    if not device.status.is_aborted(timeout=60):
        pytest.fail("Deployment did not abort")

    logger.info("Deployment aborted")
