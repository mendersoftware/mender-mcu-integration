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
LOG_MODULE_DECLARE(mender_app, LOG_LEVEL_DBG);

/* This piece of code is heavily inspired by Zephyr OS project sample:
 * https://github.com/zephyrproject-rtos/zephyr/tree/v3.7.0/samples/net/dhcpv4_client
 *
 * The main entry point, netup_wait_for_network, will set up the callbacks for the network
 * management and wait for a the device to obtain a v4 IP address. The wait is controlled with
 * a simple semaphore. */

#include <assert.h>

#include <zephyr/kernel.h>
#include <zephyr/net/net_if.h>
#include <zephyr/net/net_mgmt.h>

K_SEM_DEFINE(network_ready_sem, 0, 1);

#define DHCP_OPTION_NTP (42)

static uint8_t ntp_server[4];

static struct net_mgmt_event_callback mgmt_cb;

static struct net_dhcpv4_option_callback dhcp_cb;

static void
start_dhcpv4_client(struct net_if *iface, void *user_data) {
    ARG_UNUSED(user_data);

    LOG_INF("Start on %s: index=%d", net_if_get_device(iface)->name, net_if_get_by_iface(iface));
    net_dhcpv4_start(iface);
}

static void
event_handler(struct net_mgmt_event_callback *cb, uint32_t mgmt_event, struct net_if *iface) {
    int i = 0;

    if (mgmt_event != NET_EVENT_IPV4_ADDR_ADD) {
        return;
    }

    for (i = 0; i < NET_IF_MAX_IPV4_ADDR; i++) {
        char buf[NET_IPV4_ADDR_LEN];

        if (iface->config.ip.ipv4->unicast[i].ipv4.addr_type != NET_ADDR_DHCP) {
            continue;
        }

        LOG_INF("   Address[%d]: %s",
                net_if_get_by_iface(iface),
                net_addr_ntop(AF_INET, &iface->config.ip.ipv4->unicast[i].ipv4.address.in_addr, buf, sizeof(buf)));
        LOG_INF("    Subnet[%d]: %s", net_if_get_by_iface(iface), net_addr_ntop(AF_INET, &iface->config.ip.ipv4->unicast[i].netmask, buf, sizeof(buf)));
        LOG_INF("    Router[%d]: %s", net_if_get_by_iface(iface), net_addr_ntop(AF_INET, &iface->config.ip.ipv4->gw, buf, sizeof(buf)));
        LOG_INF("Lease time[%d]: %u seconds", net_if_get_by_iface(iface), iface->config.dhcpv4.lease_time);
    }

    // Network is up \o/
    k_sem_give(&network_ready_sem);
}

static void
option_handler(struct net_dhcpv4_option_callback *cb, size_t length, enum net_dhcpv4_msg_type msg_type, struct net_if *iface) {
    char buf[NET_IPV4_ADDR_LEN];

    LOG_INF("DHCP Option %d: %s", cb->option, net_addr_ntop(AF_INET, cb->data, buf, sizeof(buf)));
}

int
netup_wait_for_network() {
    int ret = 0;

    net_mgmt_init_event_callback(&mgmt_cb, event_handler, NET_EVENT_IPV4_ADDR_ADD);
    net_mgmt_add_event_callback(&mgmt_cb);

    net_dhcpv4_init_option_callback(&dhcp_cb, option_handler, DHCP_OPTION_NTP, ntp_server, sizeof(ntp_server));
    ret = net_dhcpv4_add_option_callback(&dhcp_cb);
    if (ret != 0) {
        return ret;
    }

    net_if_foreach(start_dhcpv4_client, NULL);

    // Wait for network
    LOG_INF("Waiting for network up...");
    return k_sem_take(&network_ready_sem, K_FOREVER);
}

void
netup_get_mac_address(char *address) {
    assert(NULL != address);

    struct net_if *iface    = net_if_get_first_up();
    assert(NULL != iface);

    struct net_linkaddr *linkaddr = net_if_get_link_addr(iface);
    assert(NULL != linkaddr);

    snprintf(address,
             18,
             "%02x:%02x:%02x:%02x:%02x:%02x",
             linkaddr->addr[0],
             linkaddr->addr[1],
             linkaddr->addr[2],
             linkaddr->addr[3],
             linkaddr->addr[4],
             linkaddr->addr[5]);
}
