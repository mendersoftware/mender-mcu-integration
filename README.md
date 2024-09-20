[![Build Status](https://gitlab.com/Northern.tech/Mender/mender-mcu-integration/badges/next/pipeline.svg)](https://gitlab.com/Northern.tech/Mender/mender-mcu-integration/pipelines)

# mender-mcu-integration

Mender is an open source over-the-air (OTA) software updater for embedded devices. Mender
comprises a client running at the embedded device, as well as a server that manages deployments
across many devices.

Mender provides modules to integrate with Real Time Operating Systems (RTOS). The code can be found
in [`mender-mcu` repository](https://github.com/mendersoftware/mender-mcu/).

This repository contains a reference project on how to integrate a user application with Mender OTA
Zephyr Module, using QEMU as the board of choice.

-------------------------------------------------------------------------------

![Mender logo](https://github.com/mendersoftware/mender/raw/master/mender_logo.png)


## Project Status

This repository is a work in progress. As we continue development, features and functionality may
evolve significantly.


## Getting started

Since the project is under active development, we recommend watching the repository or checking back
regularly for updates. Detailed documentation and usage instructions will be provided as the project
progresses.

To start using Mender, we recommend that you begin with the Getting started
section in [the Mender documentation](https://docs.mender.io/).


## Building the Zephyr Project Mender reference app

Initialize a Zephyr workspace based on this repository's manifest, which will pull Mender MCU code
and its dependencies:

```
west init workspace --manifest-url https://github.com/mendersoftware/mender-mcu-integration
cd workspace && west update
```

To built the project, you need a board that supports MCU boot. The following link will filter
the officially supported boards that also support MCU boot:

* [Zephyr Project supported boards with MCU boot](https://docs.zephyrproject.org/latest/gsearch.html?q=MCUboot&check_keywords=yes&area=default#gsc.tab=0&gsc.q=MCUboot&gsc.ref=more%3Aboards&gsc.sort=)


### ESP32-Ethernet-Kit

See board support information an [Zephyr Project
docs](https://docs.zephyrproject.org/latest/boards/espressif/esp32_ethernet_kit/doc/index.html).

This is the first board that we use as a reference given the convenience of the ethernet port
and the low price of the first generation ESP32. We will add more boards in the near future.

To build the reference project for ESP32-Ethernet-Kit, execute:
```
west build --board esp32_ethernet_kit/esp32/procpu mender-mcu-integration
```

Flash it now to the board and read the serial line with something like:
```
west flash &&  minicom -D /dev/ttyUSB1 -b 115200 -w
```

### ESP32-S3-DevKitC

To build the reference project for ESP32-Ethernet-Kit, execute:
```
west build -b esp32s3_devkitc/esp32s3/procpu mender-mcu-integration -- -DEXTRA_CONF_FILE=overlay-wifi.conf
```

Flash it now to the board and read the serial line with something like:
```
west flash && west espressif monitor
```

## First time board setup

For the first time of using the board, you need to build and flash the bootloader. It can either be
done by:

* Using `--sysbuild` option in your `west build`. Read the docs [here](https://docs.zephyrproject.org/latest/build/sysbuild/index.html).
* Building and flashing the bootloader alone following [this guide](https://docs.mcuboot.com/readme-zephyr)

Additionally, you might want to erase the whole flash so that the storage partition is clean. Use
`python -m esptool --chip esp32 erase_flash` for that. Find the vendor documentation
[here](https://docs.espressif.com/projects/esptool/en/latest/esp32/esptool/basic-commands.html#erase-flash-erase-flash-erase-region)

## Creating the Mender Artifact

Create an Artifact (remember to disable compression):

```
mender-artifact write module-image \
  --type zephyr-image \
  --file build/zephyr/zephyr.signed.bin \
  --compression none \
  --artifact-name <artifact_name> \
  --device-type <device_type>
```

## Contributing

We welcome and ask for your contribution. If you would like to contribute to
Mender, please read our guide on how to best get started
[contributing code or documentation](https://github.com/mendersoftware/mender/blob/master/CONTRIBUTING.md).


## License

Mender is licensed under the Apache License, Version 2.0. See
[LICENSE](https://github.com/mendersoftware/mender-mcu-integration/blob/master/LICENSE)
for the full license text.


## Security disclosure

We take security very seriously. If you come across any issue regarding
security, please disclose the information by sending an email to
[security@mender.io](security@mender.io). Please do not create a new public
issue. We thank you in advance for your cooperation.


## Connect with us

* Join the [Mender Hub discussion forum](https://hub.mender.io)
* Follow us on [Twitter](https://twitter.com/mender_io). Please
  feel free to tweet us questions.
* Fork us on [Github](https://github.com/mendersoftware)
* Create an issue in the [bugtracker](https://northerntech.atlassian.net/projects/MEN)
* Email us at [contact@mender.io](mailto:contact@mender.io)
* Connect to the [#mender IRC channel on Libera](https://web.libera.chat/?#mender)


## Authors

Mender was created by the team at [Northern.tech AS](https://northern.tech),
with many contributions from the community. Thanks
[everyone](https://github.com/mendersoftware/mender/graphs/contributors)!

[Mender](https://mender.io) is sponsored by [Northern.tech AS](https://northern.tech).
