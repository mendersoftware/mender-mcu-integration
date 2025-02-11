cmake_minimum_required(VERSION 3.20.0)

# This file is based on zephyr/share/sysbuild/template, just setting our default board

# Set ESP32-S3-DevkitC as the default board
set(BOARD
    "esp32s3_devkitc/esp32s3/procpu"
    CACHE
    STRING
    "Board for the Zephyr application"
)

find_package(Sysbuild REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(sysbuild LANGUAGES)
