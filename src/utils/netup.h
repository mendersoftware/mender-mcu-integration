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

#ifndef __NETUP_H__
#define __NETUP_H__

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/**
 * @brief Wait for an IP address to be leased by the DHCP server
 * @return return 0 on success, -errno on error
 */
int netup_wait_for_network();

/**
 * @brief Get MAC address
 */
void netup_get_mac_address(char *address);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* __NETUP_H__ */
