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

#include <mender/client.h>

#ifndef __MENDER_CALLBACKS_H__
#define __MENDER_CALLBACKS_H__

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/**
 * @brief Callback to be invoked in systems where the network
 * is not always available. Set to NULL if network is assumed
 * to always be ready.
 * @return return MENDER_OK on success, MENDER_FAIL on error
 */
mender_err_t mender_network_connect_cb(void);

/**
 * @brief Callback to be invoked once network operations are
 * completed. Set to NULL if network is assumed to always be
 * ready.
 * @return return MENDER_OK on success, MENDER_FAIL on error
 */
mender_err_t mender_network_release_cb(void);

/**
 * @brief Callback to post the deployment status.
 * @return return MENDER_OK on success, MENDER_FAIL on error
 */
mender_err_t mender_deployment_status_cb(mender_deployment_status_t status, char *desc);

/**
 * @brief Callback to trigger a device reset, e.g. after a
 * fatal error.
 * @return return MENDER_OK on success, MENDER_FAIL on error
 */
mender_err_t mender_restart_cb(void);

/**
 * @brief Callback to update the internal inventory of the
 * client. This inventory is sent to the Mender Server in
 * the next inventory report.
 * @return return MENDER_OK on success, MENDER_FAIL on error
 */
mender_err_t mender_get_identity_cb(const mender_identity_t **identity);

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* __MENDER_CALLBACKS_H__ */
