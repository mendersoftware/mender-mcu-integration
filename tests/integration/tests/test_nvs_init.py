# Copyright 2026 Northern.tech AS
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import os
import time
import struct
import pytest
import logging

logger = logging.getLogger(__name__)

from helpers import stdout
from device import NativeSim

################
# Flash layout
################

# native_sim emulates its flash with a plain file passed via --flash=, see
# NativeSim.start(). Mender uses storage_partition (prj.conf), which on native_sim
# is at 0xfc000 with 4 KiB sectors (zephyr/boards/native/native_sim/native_sim.dts).
# NVS takes the first CONFIG_MENDER_STORAGE_NVS_SECTOR_COUNT (default 2) sectors,
# the deployment logs FCB the rest of the partition.
FLASH_SECTOR_SIZE = 0x1000
NVS_OFFSET = 0xFC000
NVS_SECTOR_COUNT = 2
NVS_SIZE = NVS_SECTOR_COUNT * FLASH_SECTOR_SIZE
FCB_OFFSET = NVS_OFFSET + NVS_SIZE
FCB_SIZE = 0x100000 - FCB_OFFSET

# Zephyr NVS on-flash format (zephyr/subsys/kvss/nvs/nvs_priv.h): each sector
# holds data growing up from the start and Allocation Table Entries (ATEs)
# growing down from the end. The last ATE slot is the sector close ATE, the one
# before it the first entry (or the gc done ATE). An ATE is
# {u16 id, u16 offset, u16 len, u8 part, u8 crc8}, with crc8 covering only the
# ATE itself (CONFIG_NVS_DATA_CRC is off), so the data can be modified freely.
ATE_FORMAT = "<HHHBB"
ATE_SIZE = struct.calcsize(ATE_FORMAT)
ERASED_ATE = b"\xff" * ATE_SIZE

# Mender NVS IDs (src/platform/storage/zephyr/nvs/storage.c in mender-mcu)
NVS_ID_INIT_MARKER = 0
NVS_ID_PRIVATE_KEY = 1
NVS_ID_PUBLIC_KEY = 2
NVS_ID_UNUSED = 0xF0

# struct mender_storage_nvs_marker {u64 magic, u32 offset, u16 sector_size, u8 version, u8 reserved}
MARKER_FORMAT = "<QIHBB"
MARKER_MAGIC = 0x4D454E444552
MARKER_VERSION = 1
MARKER_VERSION_OFFSET = 14
EXPECTED_MARKER = struct.pack(
    MARKER_FORMAT, MARKER_MAGIC, NVS_OFFSET, FLASH_SECTOR_SIZE, MARKER_VERSION, 0
)

# Log messages
LOG_INIT_DONE = "Initialization done"
LOG_NVS_ERASING = "Mender NVS area not usable"
LOG_REASON_MOUNT_FAILED = "Mender NVS area not usable (mount failed)"
LOG_REASON_MARKER_MISMATCH = "Mender NVS area not usable (init marker mismatch)"
LOG_REASON_NO_DATA = (
    "Mender NVS area not usable (no init marker and no valid Mender data)"
)
LOG_LEGACY_DATA_KEPT = "Existing Mender data found in NVS, adding init marker"
# native_sim seeds its (fake) entropy source with a fixed value, so regenerated
# keys are identical to the previous ones and only this log tells them apart
LOG_KEYS_GENERATED = "Authentication keys not found in store"


################
# Flash helpers
################


def flash_path(device):
    return os.path.join(device.build_dir, "flash.bin")


def read_flash(device, offset, size):
    with open(flash_path(device), "rb") as f:
        f.seek(offset)
        return f.read(size)


def write_flash(device, offset, data):
    assert not device.is_running(), "Stop the device before modifying its flash"
    with open(flash_path(device), "r+b") as f:
        f.seek(offset)
        f.write(data)


def crc8_ccitt(data, crc=0xFF):
    """Same as crc8_ccitt() in zephyr/subsys/crc/crc8_sw.c"""
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def nvs_ates(device):
    """Return all valid ATEs in the NVS area as (flash offset of the ATE, id,
    flash offset of the data, data length)"""
    area = read_flash(device, NVS_OFFSET, NVS_SIZE)
    ates = []
    for sector in range(NVS_SECTOR_COUNT):
        sector_start = sector * FLASH_SECTOR_SIZE
        pos = sector_start + FLASH_SECTOR_SIZE - 2 * ATE_SIZE
        while pos >= sector_start:
            raw = area[pos : pos + ATE_SIZE]
            if raw == ERASED_ATE:
                break
            ate_id, offset, length, _, crc = struct.unpack(ATE_FORMAT, raw)
            if crc == crc8_ccitt(raw[:-1]) and ate_id != 0xFFFF:
                ates.append(
                    (
                        NVS_OFFSET + pos,
                        ate_id,
                        NVS_OFFSET + sector_start + offset,
                        length,
                    )
                )
            pos -= ATE_SIZE
    return ates


def nvs_read(device, nvs_id):
    """Return the data of the most recent entry with the given ID, or None"""
    # ATEs grow down, so the most recent entry has the lowest ATE offset
    ates = sorted(a for a in nvs_ates(device) if a[1] == nvs_id)
    if not ates:
        return None
    _, _, data_offset, length = ates[0]
    return read_flash(device, data_offset, length)


def nvs_patch_data(device, nvs_id, offset, data):
    """Overwrite the data of all entries with the given ID. The ATEs stay valid
    since their CRC does not cover the data."""
    ates = [a for a in nvs_ates(device) if a[1] == nvs_id]
    assert ates, f"No NVS entry with ID {nvs_id}"
    for _, _, data_offset, length in ates:
        assert offset + len(data) <= length
        write_flash(device, data_offset + offset, data)


def nvs_rename(device, nvs_id, new_id):
    """Move all entries with the given ID to another ID (rewriting the ATE CRC),
    i.e. make the entry disappear as if it was never written"""
    ates = [a for a in nvs_ates(device) if a[1] == nvs_id]
    assert ates, f"No NVS entry with ID {nvs_id}"
    for ate_offset, _, _, _ in ates:
        raw = bytearray(read_flash(device, ate_offset, ATE_SIZE))
        raw[0:2] = struct.pack("<H", new_id)
        raw[-1] = crc8_ccitt(raw[:-1])
        write_flash(device, ate_offset, bytes(raw))


################
# Device helpers
################


def read_log(device, until=LOG_INIT_DONE, timeout=60):
    """Read device output until a line containing `until` shows up and return all
    lines read so far. Fails the test on timeout or if the device exits first."""
    lines = []
    start_time = time.time()
    while time.time() - start_time < timeout:
        line = stdout(device)
        lines.append(line)
        if until in line:
            return lines
        if not device.is_running():
            break
    logger.debug("=== Device logs follow ===\n" + "".join(lines))
    pytest.fail(f"'{until}' not found in device output")


def log_contains(lines, text):
    return any(text in line for line in lines)


def boot(device):
    """Boot the device until the client is initialized (NVS mounted and keys
    loaded or generated), stop it and return the log lines"""
    device.start(compile=False)
    try:
        return read_log(device)
    finally:
        device.stop()


@pytest.fixture(scope="function")
def device(server, get_build_dir, mac_address):
    """A compiled (but not started) native_sim device connected to the test server"""
    device = NativeSim(get_build_dir)
    device.set_host(f"https://{server.host}")
    device.set_tenant(server.get_tenant_token())
    device.set_mac(mac_address)
    device.compile(pristine=True)
    yield device
    device.stop()


################
# Tests
################


class TestNvsInitialization:
    def test_erased_flash(self, device):
        """First boot on erased flash: no marker and no data, so the area is
        erased and the marker written. The next boot keeps the data."""
        lines = boot(device)
        assert log_contains(lines, LOG_REASON_NO_DATA)
        assert log_contains(lines, LOG_KEYS_GENERATED)
        assert nvs_read(device, NVS_ID_INIT_MARKER) == EXPECTED_MARKER
        private_key = nvs_read(device, NVS_ID_PRIVATE_KEY)
        assert private_key is not None

        lines = boot(device)
        assert not log_contains(lines, LOG_NVS_ERASING)
        assert not log_contains(lines, LOG_LEGACY_DATA_KEPT)
        assert not log_contains(lines, LOG_KEYS_GENERATED)
        assert nvs_read(device, NVS_ID_PRIVATE_KEY) == private_key

    def test_keys_kept_across_reboot(self, server, device, mac_address):
        """With a valid marker, a reboot keeps the keys, i.e. the device is still
        accepted on the server without being accepted again"""
        device.start(compile=False)
        try:
            server.accept_device(mac_address)
            device.status.is_authenticated(timeout=60)

            device.restart()
            lines = read_log(device, until="Authenticated successfully")
            assert not log_contains(lines, LOG_NVS_ERASING)
            assert not log_contains(lines, LOG_KEYS_GENERATED)
        finally:
            device.stop()

    def test_garbage_in_nvs_area(self, device):
        """NVS area filled with random data (e.g. used by another application
        before): mounting fails, the area is erased and Mender initializes.
        The deployment logs FCB after the NVS area must not be touched."""
        boot(device)
        write_flash(device, NVS_OFFSET, os.urandom(NVS_SIZE))
        fcb = read_flash(device, FCB_OFFSET, FCB_SIZE)

        lines = boot(device)
        assert log_contains(lines, LOG_REASON_MOUNT_FAILED)
        assert nvs_read(device, NVS_ID_INIT_MARKER) == EXPECTED_MARKER
        assert read_flash(device, FCB_OFFSET, FCB_SIZE) == fcb

    def test_mountable_garbage_without_marker(self, device):
        """Valid NVS with garbage under the Mender IDs and no marker: this is
        what used to be read as Mender data. It must be erased and new keys
        generated."""
        boot(device)
        nvs_rename(device, NVS_ID_INIT_MARKER, NVS_ID_UNUSED)
        nvs_patch_data(device, NVS_ID_PRIVATE_KEY, 0, b"\x00")  # not a DER SEQUENCE

        lines = boot(device)
        assert log_contains(lines, LOG_REASON_NO_DATA)
        assert log_contains(lines, LOG_KEYS_GENERATED)
        assert nvs_read(device, NVS_ID_INIT_MARKER) == EXPECTED_MARKER
        assert nvs_read(device, NVS_ID_PRIVATE_KEY)[0] == 0x30  # DER SEQUENCE again

    def test_marker_mismatch(self, device):
        """Something other than the expected marker stored under the marker ID
        (here a different version): erase"""
        boot(device)
        nvs_patch_data(
            device,
            NVS_ID_INIT_MARKER,
            MARKER_VERSION_OFFSET,
            bytes([MARKER_VERSION + 1]),
        )

        lines = boot(device)
        assert log_contains(lines, LOG_REASON_MARKER_MISMATCH)
        assert log_contains(lines, LOG_KEYS_GENERATED)
        assert nvs_read(device, NVS_ID_INIT_MARKER) == EXPECTED_MARKER

    def test_legacy_data_without_marker(self, device):
        """Device updated from an older client (valid Mender data, no marker):
        the data is kept and only the marker added"""
        boot(device)
        private_key = nvs_read(device, NVS_ID_PRIVATE_KEY)
        public_key = nvs_read(device, NVS_ID_PUBLIC_KEY)
        nvs_rename(device, NVS_ID_INIT_MARKER, NVS_ID_UNUSED)
        assert nvs_read(device, NVS_ID_INIT_MARKER) is None

        lines = boot(device)
        assert log_contains(lines, LOG_LEGACY_DATA_KEPT)
        assert not log_contains(lines, LOG_NVS_ERASING)
        assert not log_contains(lines, LOG_KEYS_GENERATED)
        assert nvs_read(device, NVS_ID_INIT_MARKER) == EXPECTED_MARKER
        assert nvs_read(device, NVS_ID_PRIVATE_KEY) == private_key
        assert nvs_read(device, NVS_ID_PUBLIC_KEY) == public_key

    def test_reset_during_erase(self, device):
        """The marker is written last, a reset in the middle of erasing an
        unusable area leads to another erase on the next boot. Simulated by a
        garbage-filled area of which only the first sector got erased."""
        boot(device)
        write_flash(device, NVS_OFFSET, os.urandom(NVS_SIZE))
        write_flash(device, NVS_OFFSET, b"\xff" * FLASH_SECTOR_SIZE)

        lines = boot(device)
        assert log_contains(lines, LOG_NVS_ERASING)
        assert log_contains(lines, LOG_KEYS_GENERATED)
        assert nvs_read(device, NVS_ID_INIT_MARKER) == EXPECTED_MARKER
        assert nvs_read(device, NVS_ID_PRIVATE_KEY) is not None
