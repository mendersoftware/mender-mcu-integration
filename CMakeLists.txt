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

# Amazon Root CA 1 certificate from https://www.amazontrust.com/repository
# Used as primary CA certificate for Hosted Mender
generate_inc_file_for_target(app
    "certs/AmazonRootCA1.cer"
    "${ZEPHYR_BINARY_DIR}/include/generated/AmazonRootCA1.cer.inc"
)

# CloudFlare CA certificate
# Used as secondary CA certificate for Artifacts
# TODO: Use Google Trust Services' root CAs instead. Rework with MEN-7550
generate_inc_file_for_target(app
    "certs/r2.cloudflarestorage.com1.crt"
    "${ZEPHYR_BINARY_DIR}/include/generated/r2.cloudflarestorage.com1.crt.inc"
)
