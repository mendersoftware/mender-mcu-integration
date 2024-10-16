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

import time
import pytest
import helpers
import subprocess

from mender_integration.tests.MenderAPI import logger

from server import Server

from helpers import get_build_folder
from helpers import get_header_file
from helpers import stdout
from device import NativeSim

import callbacks


@pytest.fixture
def common_setup():
    open(get_header_file(), "w").close()


@pytest.fixture
def teardown(request):
    yield
    subprocess.run(["rm", "-rf", get_build_folder(request)])
    subprocess.run(["rm", "-rf", get_header_file()])


def test_deployment_abort(request, teardown, common_setup):
    """
    Sample test to demonstrate use of framework
    """

    # Use hosted.mender.io for now, as there are problems with
    # the demo server
    auth_token = "..."
    server = Server(auth_token=auth_token, host="hosted.mender.io")

    device_id = "..."
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
    helpers.set_callback(callbacks.UM_DOWNLOAD_CALLBACK, download_body)

    device = NativeSim(request, stdout=True)
    # Set host and tenant in the device
    device.set_host("https://hosted.mender.io")
    device.set_tenant("...")

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
