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

#ifndef __CERTS_H__
#define __CERTS_H__

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/**
 * @brief Install TLS credentials for Hosted Mender setup
 * @return return 0 on success, -EACCES, -ENOMEM or -EEXIST on error
 * @note See https://docs.zephyrproject.org/3.7.0/doxygen/html/group__tls__credentials.html#ga640ff6dd3eb4d5017feaab6fab2bb2f7
 */
int certs_add_credentials();

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* __CERTS_H__ */
