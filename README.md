[![Build Status](https://gitlab.com/Northern.tech/Mender/mender-mcu-integration/badges/main/pipeline.svg)](https://gitlab.com/Northern.tech/Mender/mender-mcu-integration/pipelines)

# mender-mcu-integration

Mender is an open source over-the-air (OTA) software updater for embedded devices. Mender
comprises a client running at the embedded device, as well as a server that manages deployments
across many devices.

Mender provides modules to integrate with Real Time Operating Systems (RTOS). The code can be found
in [`mender-mcu` repository](https://github.com/mendersoftware/mender-mcu/).

This repository contains a reference project on how to integrate a user application with Mender OTA
Zephyr Module, with configurations for some boards to choose from.

-------------------------------------------------------------------------------

![Mender logo](https://github.com/mendersoftware/mender/raw/master/mender_logo.png)


## Get started

To get started with Mender for Microcontrollers, visit [Mender documentation](https://docs.mender.io/get-started/microcontroller-preview).

### Native simulator

See board support information from [Zephyr Project
docs](https://docs.zephyrproject.org/latest/boards/native/native_sim/doc/index.html).

*WARNING*: this board does not support MCUBoot, so the default "zephyr-image" Update Module is not
compiled in, but rather "noop-update", which does nothing. This is meant to be used for testing purposes only.

To set up networking, run `net-setup.sh` from `/path/to/workspace/tools/net-tools`, and see
instructions in the
[Zephyr documentation](https://docs.zephyrproject.org/latest/connectivity/networking/qemu_setup.html#setting-up-zephyr-and-nat-masquerading-on-host-to-access-internet)
on how to configure the host machine to access internet.

To build the reference project for native_sim, execute:
```
west build --board native_sim mender-mcu-integration
```

Then you can run the binary with:
```
./build/zephyr/zephyr.exe
```

or
```
west build -t run
```

### Using on-premise demo Mender Server

To run the Native Simulator with on-premise Mender Server:

1. Follow instructions from [mender-server](https://github.com/mendersoftware/mender-server) to start the server

2. Copy and convert the demo certificate for docker.mender.io
    ```
    wget https://raw.githubusercontent.com/mendersoftware/mender-server/main/compose/certs/mender.crt
    openssl x509 -in mender.crt -outform der -out mender.der
    ```

3. Add the following Kconfig parameters to your build:
    ```
    CONFIG_MENDER_SERVER_HOST_ON_PREM=y
    CONFIG_MENDER_SERVER_HOST="https://docker.mender.io"
    CONFIG_MENDER_APP_SERVER_HOST_ON_PREM_CERT="mender.der"
    CONFIG_DNS_SERVER_IP_ADDRESSES=y
    CONFIG_DNS_SERVER1="192.0.2.2:15353"
    ```

4. Start networking with  `net-setup.sh`

5. Start the DNS and DHCP servers with `dnsmasq`
    ```
    cat << EOF > dnsmasq.conf
    # Config for Mender Demo Server DNS and DHCPv4
    interface=zeth

    port=15353
    bind-interfaces
    no-resolv

    address=/docker.mender.io/192.0.2.2
    dhcp-range=192.0.2.16,192.0.2.32,1h
    EOF
    sudo dnsmasq -C dnsmasq.conf -d
    ```

6. Launch the Mender MCU client \o/

    ```
    west build -t run
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
