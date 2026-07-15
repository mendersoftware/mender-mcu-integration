// Copyright 2026 Northern.tech AS
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

#include "esp_log.h"
#include "esp_system.h"

#include "mender/client.h"
#include "mender/utils.h"

static const char *TAG = "mender_app";

static mender_identity_t identity = { .name = "mac", .value = "00:11:22:33:44:55" };

static mender_err_t
get_identity_cb(const mender_identity_t **id) {
    *id = &identity;
    return MENDER_OK;
}

static mender_err_t
network_connect_cb(void) {
    return MENDER_OK;
}

static mender_err_t
network_release_cb(void) {
    return MENDER_OK;
}

static mender_err_t
deployment_status_cb(mender_deployment_status_t status, const char *desc) {
    ESP_LOGI(TAG, "deployment status %d (%s)", (int)status, desc ? desc : "");
    return MENDER_OK;
}

static mender_err_t
restart_cb(void) {
    esp_restart();
    return MENDER_OK;
}

void
app_main(void) {
    ESP_LOGI(TAG, "Hello World! %s", CONFIG_IDF_TARGET);

    /* Server host, tenant token, device type etc. come from the component
     * configuration, overridable with idf.py -D */
    mender_client_config_t config = {
        .update_poll_interval = 1800,
    };

    ESP_LOGI(TAG, "Initializing Mender Client with:");
    ESP_LOGI(TAG, "   Identity:      '{\"%s\": \"%s\"}'", identity.name, identity.value);
    mender_client_callbacks_t callbacks = {
        .network_connect   = network_connect_cb,
        .network_release   = network_release_cb,
        .deployment_status = deployment_status_cb,
        .restart           = restart_cb,
        .get_identity      = get_identity_cb,
    };

    mender_err_t ret = mender_client_init(&config, &callbacks);
    ESP_LOGI(TAG, "mender_client_init returned %d", (int)ret);
    if (MENDER_OK != ret) {
        return;
    }

    /* Not reached until MEN-9961 replaces the weak scheduler */
    ret = mender_client_activate();
    ESP_LOGI(TAG, "mender_client_activate returned %d", (int)ret);
}
