cmake_minimum_required(VERSION 3.20.0)

# ESP32-S3-DevkitC is the default board
set(BOARD
    "esp32s3_devkitc/esp32s3/procpu"
    CACHE
    STRING
    "Board for the Zephyr application"
)

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

# Install certificates if a hosted Mender server is selected
if (CONFIG_MENDER_SERVER_HOST_US OR CONFIG_MENDER_SERVER_HOST_EU)
    # Links to certificates used for hosted Mender US
    if (CONFIG_MENDER_SERVER_HOST_US)
        set(PRIMARY_CERTIFICATE_LINK "https://www.amazontrust.com/repository/AmazonRootCA1.cer")
        set(PRIMARY_CERTIFICATE_SHA256 "8ecde6884f3d87b1125ba31ac3fcb13d7016de7f57cc904fe1cb97c6ae98196e")

        set(SECONDARY_CERTIFICATE_LINK "https://i.pki.goog/r4.crt")
        set(SECONDARY_CERTIFICATE_SHA256 "349dfa4058c5e263123b398ae795573c4e1313c83fe68f93556cd5e8031b3c7d")
    # Links to certificates used for hosted Mender EU
    elseif (CONFIG_MENDER_SERVER_HOST_EU)
        set(PRIMARY_CERTIFICATE_LINK "https://letsencrypt.org/certs/isrgrootx1.der")
        set(PRIMARY_CERTIFICATE_SHA256 "96bcec06264976f37460779acf28c5a7cfe8a3c0aae11a8ffcee05c0bddf08c6")

        set(SECONDARY_CERTIFICATE_LINK "https://i.pki.goog/r4.crt")
        set(SECONDARY_CERTIFICATE_SHA256 "349dfa4058c5e263123b398ae795573c4e1313c83fe68f93556cd5e8031b3c7d")
    endif()

    set(PRIMARY_CERTIFICATE "${CMAKE_CURRENT_BINARY_DIR}/PrimaryCertificate.cer")
    file(DOWNLOAD ${PRIMARY_CERTIFICATE_LINK} ${PRIMARY_CERTIFICATE} EXPECTED_HASH SHA256=${PRIMARY_CERTIFICATE_SHA256})
    add_custom_target(certificate_one DEPENDS ${PRIMARY_CERTIFICATE})
    add_dependencies(app certificate_one)

    set(SECONDARY_CERTIFICATE "${CMAKE_CURRENT_BINARY_DIR}/SecondaryCertificate.cer")
    file(DOWNLOAD ${SECONDARY_CERTIFICATE_LINK} ${SECONDARY_CERTIFICATE} EXPECTED_HASH SHA256=${SECONDARY_CERTIFICATE_SHA256})
    add_custom_target(certificate_two DEPENDS ${SECONDARY_CERTIFICATE})
    add_dependencies(app certificate_two)

    generate_inc_file_for_target(app
        ${PRIMARY_CERTIFICATE}
        "${ZEPHYR_BINARY_DIR}/include/generated/PrimaryCertificate.cer.inc"
    )

    generate_inc_file_for_target(app
        ${SECONDARY_CERTIFICATE}
        "${ZEPHYR_BINARY_DIR}/include/generated/SecondaryCertificate.cer.inc"
    )
endif()
file(COPY_FILE "config-tls-mender.h" "${ZEPHYR_BINARY_DIR}/include/generated/config-tls-mender.h")
