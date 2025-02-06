cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(mender-mcu-integration)

target_sources(app PRIVATE
    src/main.c
    src/utils/netup.c
    src/utils/certs.c
)

target_include_directories(app PUBLIC
    src
)

if(CONFIG_MENDER_APP_NOOP_UPDATE_MODULE MATCHES "y")
    target_sources(app PRIVATE src/modules/noop-update-module.c)
endif()

option(BUILD_INTEGRATION_TESTS "Enable integration tests" OFF)

if(BUILD_INTEGRATION_TESTS)
    target_compile_definitions(app PRIVATE BUILD_INTEGRATION_TESTS)
    target_include_directories(app PUBLIC tests/integration/src)
    target_sources(app PRIVATE tests/integration/src/modules/test-update-module.c)
    target_sources(app PRIVATE tests/integration/src/callbacks.c)
endif()

# Amazon Root CA 1 certificate from https://www.amazontrust.com/repository
# Used as primary CA certificate for Hosted Mender
generate_inc_file_for_target(app
    "certs/AmazonRootCA1.cer"
    "${ZEPHYR_BINARY_DIR}/include/generated/AmazonRootCA1.cer.inc"
)

# Google Trust Services GTS Root R4 from https://pki.goog/repository
# Used as secondary CA certificate for Artifacts from Hosted Mender
generate_inc_file_for_target(app
    "certs/GoogleRootR4.cer"
    "${ZEPHYR_BINARY_DIR}/include/generated/GoogleRootR4.cer.inc"
)

file(COPY_FILE "config-tls-mender.h" "${ZEPHYR_BINARY_DIR}/include/generated/config-tls-mender.h")
