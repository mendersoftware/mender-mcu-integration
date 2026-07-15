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

/* This piece of code is heavily inspired by the ESP-IDF station example:
 * https://github.com/espressif/esp-idf/tree/master/examples/wifi/getting_started/station */

#include "netup.h"

#include <stdio.h>

#include "esp_event.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "nvs_flash.h"

static const char *TAG = "mender_app";

static SemaphoreHandle_t network_ready_sem;

static void
event_handler(void *arg, esp_event_base_t event_base, int32_t event_id, void *event_data) {
    if ((WIFI_EVENT == event_base) && (WIFI_EVENT_STA_START == event_id)) {
        esp_wifi_connect();
    } else if ((WIFI_EVENT == event_base) && (WIFI_EVENT_STA_DISCONNECTED == event_id)) {
        ESP_LOGI(TAG, "Disconnected, reconnecting to %s...", CONFIG_MENDER_APP_WIFI_SSID);
        esp_wifi_connect();
    } else if ((IP_EVENT == event_base) && (IP_EVENT_STA_GOT_IP == event_id)) {
        ip_event_got_ip_t *event = (ip_event_got_ip_t *)event_data;
        ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&event->ip_info.ip));
        xSemaphoreGive(network_ready_sem);
    }
}

int
netup_wait_for_network(void) {
    network_ready_sem = xSemaphoreCreateBinary();
    if (NULL == network_ready_sem) {
        return -1;
    }

    /* The Wi-Fi driver stores calibration data in NVS */
    esp_err_t err = nvs_flash_init();
    if (ESP_ERR_NVS_NO_FREE_PAGES == err || ESP_ERR_NVS_NEW_VERSION_FOUND == err) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t init_config = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&init_config));

    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &event_handler, NULL));

    wifi_config_t wifi_config = {
        .sta = {
            .ssid     = CONFIG_MENDER_APP_WIFI_SSID,
            .password = CONFIG_MENDER_APP_WIFI_PSK,
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "Connecting to wireless network %s...", CONFIG_MENDER_APP_WIFI_SSID);
    if (pdTRUE != xSemaphoreTake(network_ready_sem, portMAX_DELAY)) {
        return -1;
    }

    return 0;
}

void
netup_get_mac_address(char *address) {
    uint8_t mac[6];
    ESP_ERROR_CHECK(esp_read_mac(mac, ESP_MAC_WIFI_STA));
    sprintf(address, "%02x:%02x:%02x:%02x:%02x:%02x", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}
