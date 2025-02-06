// Copyright 2025 Northern.tech AS
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

#include "utils/callbacks.h"
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(integration_test, LOG_LEVEL_DBG);

mender_err_t
mender_network_connect_cb(void) {
    LOG_DBG("network_connect_cb");
#ifdef NETWORK_CONNECT_CALLBACK
    NETWORK_CONNECT_CALLBACK();
#endif
    return MENDER_OK;
}

mender_err_t
mender_network_release_cb(void) {
    LOG_DBG("network_release_cb");
#ifdef NETWORK_RELEASE_CALLBACK
    NETWORK_RELEASE_CALLBACK();
#endif
    return MENDER_OK;
}

mender_err_t
mender_deployment_status_cb(mender_deployment_status_t status, char *desc) {
    LOG_DBG("deployment_status_cb: %s", desc);
#ifdef DEPLOYMENT_STATUS_CALLBACK
    DEPLOYMENT_STATUS_CALLBACK();
#endif
    return MENDER_OK;
}

mender_err_t
mender_restart_cb(void) {
    LOG_DBG("restart_cb");
#ifdef RESTART_CALLBACK
    RESTART_CALLBACK();
#endif
    return MENDER_OK;
}

#ifndef MAC_ADDRESS
#define MAC_ADDRESS "11:11:22:33:55:88"
#endif /* MAC_ADDRESS */
static char mac_address[18] = MAC_ADDRESS;

static mender_identity_t mender_identity = { .name = "mac", .value = mac_address };

mender_err_t
mender_get_identity_cb(const mender_identity_t **identity) {
    LOG_DBG("get_identity_cb");
#ifdef GET_IDENTITY_CALLBACK
    GET_IDENTITY_CALLBACK();
#else
    if (NULL != identity) {
        *identity = &mender_identity;
        return MENDER_OK;
    }
#endif
    return MENDER_FAIL;
}
