// Copyright 2024 Northern.tech AS
//
//    Licensed under the Apache License, Version 2.0 (the "License");
//    you may not use this file except in compliance with the License.
//    You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//    Unless required by applicable law or agreed to in writing, software
//    distributed under the License is distributed on an "AS IS" BASIS,
//    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//    See the License for the specific language governing permissions and
//    limitations under the License.

#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(mender_mcu_integration, LOG_LEVEL_DBG);

#include <zephyr/kernel.h>

#include "mender-client.h"
#include "mender-inventory.h"
#include "mender-flash.h"

static mender_err_t
network_connect_cb(void) {
    LOG_INF("network_connect_cb");
    return MENDER_OK;
}

static mender_err_t
network_release_cb(void) {
    LOG_INF("network_release_cb");
    return MENDER_OK;
}

static mender_err_t
authentication_success_cb(void) {
    LOG_INF("authentication_success_cb");
    return MENDER_OK;
}

static mender_err_t
authentication_failure_cb(void) {
    LOG_INF("authentication_failure_cb");
    return MENDER_OK;
}

static mender_err_t
deployment_status_cb(mender_deployment_status_t status, char *desc) {
    LOG_INF("deployment_status_cb");
    return MENDER_OK;
}

static mender_err_t
restart_cb(void) {
    LOG_INF("restart_cb");
    return MENDER_OK;
}

static mender_err_t
get_identity_cb(mender_identity_t **identity) {
    static mender_identity_t mender_identity = { .name = "mac", .value = "aa:bb:cc:dd:ee:ff" };
    if (NULL != identity) {
        *identity = &mender_identity;
        return MENDER_OK;
    }
    return MENDER_FAIL;
}

int
main(void) {
    printf("Hello World! %s\n", CONFIG_BOARD_TARGET);

    /* Initialize mender-client */
    mender_client_config_t    mender_client_config    = { .artifact_name                = "artifact_name",
                                                          .device_type                  = "device_type",
                                                          .host                         = "https://hosted.mender.io",
                                                          .tenant_token                 = "my-secret-token",
                                                          .authentication_poll_interval = 300,
                                                          .update_poll_interval         = 600,
                                                          .recommissioning              = false };
    mender_client_callbacks_t mender_client_callbacks = { .network_connect        = network_connect_cb,
                                                          .network_release        = network_release_cb,
                                                          .authentication_success = authentication_success_cb,
                                                          .authentication_failure = authentication_failure_cb,
                                                          .deployment_status      = deployment_status_cb,
                                                          .restart                = restart_cb,
                                                          .get_identity           = get_identity_cb,
                                                          .get_user_provided_keys = NULL };

    assert(MENDER_OK == mender_client_init(&mender_client_config, &mender_client_callbacks));
    LOG_INF("Mender client initialized");

#ifdef CONFIG_MENDER_CLIENT_ADD_ON_INVENTORY
    mender_keystore_t inventory[] = { { .name = "demo", .value = "demo" }, { .name = "foo", .value = "var" }, { .name = NULL, .value = NULL } };
    assert(MENDER_OK == mender_inventory_set(inventory));
    LOG_INF("Mender inventory set");
#endif /* CONFIG_MENDER_CLIENT_ADD_ON_INVENTORY */

    assert(MENDER_OK == mender_client_activate());
    LOG_INF("Mender client activated");

    k_sleep(K_MSEC(10000));

    /* Deactivate and release mender-client */
    mender_client_deactivate();
    mender_client_exit();

    return 0;
}
