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

**TODO**: Rework instructions once `mender-mcu` and `mender-mcu-integration` repo are public.

To add Mender OTA Zephyr Module on your project, create first a vanilla Zephyr workspace and
manually set the manifest to point to this repository.

```
west init workspace
cd workspace
git clone git@github.com:mendersoftware/mender-mcu-integration
sed  -i .west/config -e 's|path = zephyr|path = mender-mcu-integration|'
west update
```

*In the future this will look like*

```
west init workspace --manifest-url https://github.com/mendersoftware/mender-mcu-integration
cd workspace && west update
```

Now build and run the reference application with:

:warning: Work in progress :warning:

```
west build --build-dir build-qemu --board qemu_x86 mender-mcu-integration
west build --build-dir build-qemu --target run
```


## Contributing

We welcome and ask for your contribution. If you would like to contribute to
Mender, please read our guide on how to best get started
[contributing code or documentation](https://github.com/mendersoftware/mender/blob/master/CONTRIBUTING.md).


## License

Mender is licensed under the Apache License, Version 2.0. See
[LICENSE](https://github.com/mendersoftware/mender-convert/blob/master/LICENSE)
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
