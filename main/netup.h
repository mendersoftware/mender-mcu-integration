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

#ifndef __NETUP_H__
#define __NETUP_H__

/**
 * @brief Connect to the wireless network and wait for an IP address
 * @return 0 on success, -1 on error
 */
int netup_wait_for_network(void);

/**
 * @brief Get MAC address
 */
void netup_get_mac_address(char *address);

#endif /* __NETUP_H__ */
