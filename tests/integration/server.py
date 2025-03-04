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
import logging

from helpers import get_uncompressed_mender_artifact

import logging

logger = logging.getLogger(__name__)

URL_DEPLOYMENTS_STATUS = "/deployments/{id}/status"
from mender_server.backend.tests.integration.testutils.api.client import ApiClient
from mender_server.backend.tests.integration.testutils.api import deployments

from mender_server.backend.tests.integration.testutils.api import (
    useradm,
    deviceauth,
)


class Server:
    def __init__(self, auth_token, host="docker.mender.io"):
        self.auth_token = auth_token
        self.host = host
        self.deployment_id = ""
        self.device_id = ""

        self.api_dev_deploy = ApiClient(deployments.URL_MGMT, self.host)
        self.devauthm = ApiClient(deviceauth.URL_MGMT, host=self.host)

    def get_pending_devices(self):
        # Get pending devices
        qs_params = {"page": 1, "per_page": 64, "status": "pending"}
        r = self.devauthm.with_auth(os.getenv("TEST_AUTH_TOKEN")).call(
            "GET", deviceauth.URL_MGMT_DEVICES, qs_params=qs_params
        )
        assert r.status_code == 200
        return r.json()

    def is_accepted(self, mac_address):
        r = self.devauthm.with_auth(os.getenv("TEST_AUTH_TOKEN")).call(
            "GET", deviceauth.URL_MGMT_DEVICES
        )
        assert r.status_code == 200
        for device in (dev for dev in r.json() if dev["identity_data"] is not None):
            if device["identity_data"]["mac"] == mac_address:
                self.device_id = device["id"]
                return True
        return False

    def accept_device(self, mac_address="11:11:22:33:55:88"):
        if self.is_accepted(mac_address):
            return
        pending_devices = self.get_pending_devices()
        timeout = 10
        while not pending_devices and timeout > 0:
            pending_devices = self.get_pending_devices()
            time.sleep(1)
            timeout -= 1

        for device in pending_devices:
            device_id = device["id"]
            auth_set_id = device["auth_sets"][0]["id"]
            identity_data = device["identity_data"]
            if identity_data["mac"] == mac_address:
                self.device_id = device_id
                r = self.devauthm.with_auth(os.getenv("TEST_AUTH_TOKEN")).call(
                    "PUT",
                    deviceauth.URL_AUTHSET_STATUS,
                    deviceauth.req_status("accepted"),
                    path_params={"did": device_id, "aid": auth_set_id},
                )
                assert r.status_code == 204

    def abort_deployment(self):
        logger.info("Aborting deployment")
        return self.api_dev_deploy.with_auth(self.auth_token).call(
            "PUT",
            URL_DEPLOYMENTS_STATUS.format(id=self.deployment_id),
            body={"status": "aborted"},
        )

    def create_deployment(self, artifact_name, device_id, force=False):
        logger.info("Creating deployment")
        response = self.api_dev_deploy.with_auth(self.auth_token).call(
            "POST",
            deployments.URL_DEPLOYMENTS,
            body={
                "name": artifact_name,
                "artifact_name": artifact_name,
                "devices": [device_id],
                "force_installation": force,
            },
        )
        assert response.status_code == 201, f"{response.text} {response.status_code}"
        self.deployment_id = os.path.basename(response.headers["Location"])

    def upload_artifact(self, name, device_types):
        with get_uncompressed_mender_artifact(
            name, device_types=device_types, update_module="test-update"
        ) as filename:

            upload_image(filename, self.auth_token, self.api_dev_deploy)

            deployment_req = {
                "name": name,
                "artifact_name": name,
            }

            self.api_dev_deploy.with_auth(self.auth_token).call(
                "POST", deployments.URL_DEPLOYMENTS, deployment_req
            )
        return name


def upload_image(filename, auth_token, api_client):
    api_client.headers = {}
    r = api_client.with_auth(auth_token).call(
        "POST",
        deployments.URL_DEPLOYMENTS_ARTIFACTS,
        files=(
            ("description", (None)),
            ("size", (None, str(os.path.getsize(filename)))),
            ("artifact", (filename, open(filename, "rb"), "application/octet-stream")),
        ),
    )
