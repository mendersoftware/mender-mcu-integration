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
import redo
import logging

from helpers import get_uncompressed_mender_artifact

import logging

logger = logging.getLogger(__name__)

URL_DEPLOYMENTS_STATUS = "/deployments/{id}/status"
from mender_server.backend.tests.testutils.api.client import ApiClient
from mender_server.backend.tests.testutils.api import deployments

from mender_server.backend.tests.testutils.api import (
    tenantadm,
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
        self.tenantadm = ApiClient(tenantadm.URL_MGMT, host=self.host)

    def get_pending_devices(self):
        # Get pending devices
        qs_params = {"page": 1, "per_page": 64, "status": "pending"}
        r = self.devauthm.with_auth(os.getenv("TEST_AUTH_TOKEN")).call(
            "GET", deviceauth.URL_MGMT_DEVICES, qs_params=qs_params
        )
        assert r.status_code == 200
        return r.json()

    def get_tenant_token(self):
        r = self.tenantadm.with_auth(os.getenv("TEST_AUTH_TOKEN")).call(
            "GET", tenantadm.URL_MGMT_THIS_TENANT
        )
        assert r.status_code == 200
        return r.json()["tenant_token"]

    @redo.retriable(sleeptime=5, attempts=6)
    def accept_device(self, mac_address):
        for device in self.get_pending_devices():
            identity_data = device.get("identity_data") or {}
            if identity_data.get("mac") != mac_address:
                continue
            self.device_id = device["id"]
            auth_set_id = device["auth_sets"][0]["id"]
            r = self.devauthm.with_auth(os.getenv("TEST_AUTH_TOKEN")).call(
                "PUT",
                deviceauth.URL_AUTHSET_STATUS,
                deviceauth.req_status("accepted"),
                path_params={"did": self.device_id, "aid": auth_set_id},
            )
            assert r.status_code == 204
            return
        raise AssertionError(f"No pending device with mac {mac_address} found")

    def decommission_device(self):
        if not self.device_id:
            return
        r = self.devauthm.with_auth(os.getenv("TEST_AUTH_TOKEN")).call(
            "DELETE",
            deviceauth.URL_DEVICE,
            path_params={"id": self.device_id},
        )
        assert r.status_code in (204, 404), f"{r.text} {r.status_code}"
        self.device_id = ""
        self.deployment_id = ""

    def abort_deployment(self):
        if not self.deployment_id:
            return
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
