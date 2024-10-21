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

#include "mender-client.h"
#include "mender-log.h"
#include "mender-utils.h"
#include "mender-update-module.h"
#include <stdio.h>
#include <stdlib.h>

#include "zephyr/kernel.h"

#include "mender-utils.h"

#include <zephyr/kernel.h>

#include "test_definitions.h"

static mender_err_t test_update_module_download(mender_update_state_t state, mender_update_state_data_t callback_data);

static mender_err_t test_update_module_install(mender_update_state_t state, mender_update_state_data_t callback_data);

static mender_err_t test_update_module_reboot(mender_update_state_t state, mender_update_state_data_t callback_data);

static mender_err_t test_update_module_verify_reboot(mender_update_state_t state, mender_update_state_data_t callback_data);

static mender_err_t test_update_module_commit(mender_update_state_t state, mender_update_state_data_t callback_data);

static mender_err_t test_update_module_rollback(mender_update_state_t state, mender_update_state_data_t callback_data);

static mender_err_t test_update_module_failure(mender_update_state_t state, mender_update_state_data_t callback_data);

static mender_err_t test_update_module_rollback_reboot(mender_update_state_t state, mender_update_state_data_t callback_data);

#ifndef UM_REQUIRES_REBOOT
#define UM_REQUIRES_REBOOT false
#endif
#ifndef UM_SUPPORTS_ROLLBACK
#define UM_SUPPORTS_ROLLBACK false
#endif

mender_err_t
test_update_module_register(void) {
    mender_err_t            ret;
    mender_update_module_t *test_update_module;

    /* Register the zephyr-image update module */
    if (NULL == (test_update_module = calloc(1, sizeof(mender_update_module_t)))) {
        mender_log_error("Unable to allocate memory for the 'test-update' update module");
        return MENDER_FAIL;
    }
    test_update_module->callbacks[MENDER_UPDATE_STATE_DOWNLOAD]        = &test_update_module_download;
    test_update_module->callbacks[MENDER_UPDATE_STATE_INSTALL]         = &test_update_module_install;
    test_update_module->callbacks[MENDER_UPDATE_STATE_REBOOT]          = &test_update_module_reboot;
    test_update_module->callbacks[MENDER_UPDATE_STATE_VERIFY_REBOOT]   = &test_update_module_verify_reboot;
    test_update_module->callbacks[MENDER_UPDATE_STATE_COMMIT]          = &test_update_module_commit;
    test_update_module->callbacks[MENDER_UPDATE_STATE_ROLLBACK]        = &test_update_module_rollback;
    test_update_module->callbacks[MENDER_UPDATE_STATE_FAILURE]         = &test_update_module_failure;
    test_update_module->callbacks[MENDER_UPDATE_STATE_ROLLBACK_REBOOT] = &test_update_module_rollback_reboot;
    test_update_module->artifact_type                                  = "test-update";
    test_update_module->requires_reboot                                = UM_REQUIRES_REBOOT;
    test_update_module->supports_rollback                              = UM_SUPPORTS_ROLLBACK;

    if (MENDER_OK != (ret = mender_client_register_update_module(test_update_module))) {
        mender_log_error("Unable to register the 'test-update' update module");
        /* mender_client_register_update_module() takes ownership if it succeeds */
        free(test_update_module);
        return ret;
    }

    return MENDER_OK;
}

static mender_err_t
test_update_module_download(MENDER_NDEBUG_UNUSED mender_update_state_t state, MENDER_ARG_UNUSED mender_update_state_data_t callback_data) {

    /* Macro defined by test */
#ifdef UM_DOWNLOAD_CALLBACK
    UM_DOWNLOAD_CALLBACK();
#endif

    return MENDER_OK;
}

static mender_err_t
test_update_module_install(MENDER_NDEBUG_UNUSED mender_update_state_t state, MENDER_ARG_UNUSED mender_update_state_data_t callback_data) {

    /* Macro defined by test */
#ifdef UM_INSTALL_CALLBACK
    UM_INSTALL_CALLBACK();
#endif
    return MENDER_OK;
}

static mender_err_t test_update_module_reboot(mender_update_state_t state, mender_update_state_data_t callback_data) {

    /* Macro defined by test */
#ifdef UM_REBOOT_CALLBACK
    UM_REBOOT_CALLBACK();
#endif
    return MENDER_OK;
}

static mender_err_t test_update_module_verify_reboot(mender_update_state_t state, mender_update_state_data_t callback_data) {

    /* Macro defined by test */
#ifdef UM_VERIFY_REBOOT_CALLBACK
    UM_VERIFY_REBOOT_CALLBACK();
#endif

    return MENDER_OK;
}

static mender_err_t
test_update_module_commit(MENDER_NDEBUG_UNUSED mender_update_state_t state, MENDER_ARG_UNUSED mender_update_state_data_t callback_data) {

    /* Macro defined by test */
#ifdef UM_COMMIT_CALLBACK
    UM_COMMIT_CALLBACK();
#endif

    return MENDER_OK;
}


static mender_err_t test_update_module_rollback(mender_update_state_t state, mender_update_state_data_t callback_data) {

    /* Macro defined by test */
#ifdef UM_ROLLBACK_CALLBACK
    UM_ROLLBACK_CALLBACK();
#endif

    return MENDER_OK;
}

static mender_err_t
test_update_module_failure(MENDER_NDEBUG_UNUSED mender_update_state_t state, MENDER_ARG_UNUSED mender_update_state_data_t callback_data) {

    /* Macro defined by test */
#ifdef UM_FAILURE_CALLBACK
    UM_FAILURE_CALLBACK();
#endif

    return MENDER_OK;
}


static mender_err_t test_update_module_rollback_reboot(mender_update_state_t state, mender_update_state_data_t callback_data) {

    /* Macro defined by test */
#ifdef UM_ROLLBACK_REBOOT_CALLBACK
    UM_ROLLBACK_REBOOT_CALLBACK();
#endif
    return MENDER_OK;
}
