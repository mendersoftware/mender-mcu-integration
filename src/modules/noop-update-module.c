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

#include <mender/alloc.h>
#include <mender/client.h>
#include <mender/log.h>
#include <mender/utils.h>
#include <mender/update-module.h>

static mender_err_t noop_update_module_download(mender_update_state_t state, mender_update_state_data_t callback_data);

static mender_err_t noop_update_module_install(mender_update_state_t state, mender_update_state_data_t callback_data);

static mender_err_t noop_update_module_commit(mender_update_state_t state, mender_update_state_data_t callback_data);

static mender_err_t noop_update_module_failure(mender_update_state_t state, mender_update_state_data_t callback_data);

mender_err_t
noop_update_module_register(void) {
    mender_err_t            ret;
    mender_update_module_t *noop_update_module;

    /* Register the zephyr-image update module */
    if (NULL == (noop_update_module = mender_calloc(1, sizeof(mender_update_module_t)))) {
        mender_log_error("Unable to allocate memory for the 'zephyr-image' update module");
        return MENDER_FAIL;
    }
    noop_update_module->callbacks[MENDER_UPDATE_STATE_DOWNLOAD]        = &noop_update_module_download;
    noop_update_module->callbacks[MENDER_UPDATE_STATE_INSTALL]         = &noop_update_module_install;
    noop_update_module->callbacks[MENDER_UPDATE_STATE_REBOOT]          = NULL;
    noop_update_module->callbacks[MENDER_UPDATE_STATE_VERIFY_REBOOT]   = NULL;
    noop_update_module->callbacks[MENDER_UPDATE_STATE_COMMIT]          = &noop_update_module_commit;
    noop_update_module->callbacks[MENDER_UPDATE_STATE_ROLLBACK]        = NULL;
    noop_update_module->callbacks[MENDER_UPDATE_STATE_FAILURE]         = &noop_update_module_failure;
    noop_update_module->callbacks[MENDER_UPDATE_STATE_ROLLBACK_REBOOT] = NULL;
    noop_update_module->artifact_type                                  = "noop-update";
    noop_update_module->requires_reboot                                = false;
    noop_update_module->supports_rollback                              = false;

    if (MENDER_OK != (ret = mender_update_module_register(noop_update_module))) {
        mender_log_error("Unable to register the 'noop-update' update module");
        /* mender_update_module_register() takes ownership if it succeeds */
        free(noop_update_module);
        return ret;
    }

    return MENDER_OK;
}

static mender_err_t
noop_update_module_download(MENDER_NDEBUG_UNUSED mender_update_state_t state, MENDER_ARG_UNUSED mender_update_state_data_t callback_data) {
    assert(MENDER_UPDATE_STATE_DOWNLOAD == state);

    /* Purpose: flash the update somewhere. This callback will be called consequently for each block
       downloaded by the Mender client. See mender_update_state_data_t */

    return MENDER_OK;
}

static mender_err_t
noop_update_module_install(MENDER_NDEBUG_UNUSED mender_update_state_t state, MENDER_ARG_UNUSED mender_update_state_data_t callback_data) {
    assert(MENDER_UPDATE_STATE_INSTALL == state);

    /* Purpose: install or activate the update. Until this point the download is not verified so
       it has ben saved somewhere either temporary or in its final destination but inactive. */

    return MENDER_OK;
}

static mender_err_t
noop_update_module_commit(MENDER_NDEBUG_UNUSED mender_update_state_t state, MENDER_ARG_UNUSED mender_update_state_data_t callback_data) {
    assert(MENDER_UPDATE_STATE_COMMIT == state);

    /* Purpose: commit the update. We are done */

    return MENDER_OK;
}

static mender_err_t
noop_update_module_failure(MENDER_NDEBUG_UNUSED mender_update_state_t state, MENDER_ARG_UNUSED mender_update_state_data_t callback_data) {
    assert(MENDER_UPDATE_STATE_FAILURE == state);

    /* Purpose: abort the update. We are done */

    return MENDER_OK;
}
