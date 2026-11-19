## Running the integration tests locally

### Pre-requisites:
 - networking for the native-sim board (see README)
 - mender-artifact

The two following commands assumes you're in `tests/integration`:

Python requirements from mender-server
- `pip install -r mender_server/backend/tests/requirements-integration.txt`

Requirements from zephyr
- `pip install -r ../../../zephyr/scripts/requirements-base.txt`

### Running tests
To run the current tests, you will need to export
 - TEST_AUTH_TOKEN

as these are used to connect to hosted Mender.

Run `git submodule update --init --recursive`.

Run the tests with `pytest -s --host hosted.mender.io` in the `tests/integration` directory.

### Running tests with AddressSanitizer
Add `--sanitize` to build the device with `CONFIG_ASAN=y` (AddressSanitizer
and LeakSanitizer):

`pytest -s --host hosted.mender.io --sanitize`

In this mode Mender's allocations are routed to the host `malloc()` (see
`src/host_alloc.c`) so ASAN can track the Mender heap. Sanitizer reports are
written to `<build_dir>/asan.<pid>` and any report fails the test that produced
it. Leaks are reported when the device exits, which happens on `device.stop()`.
Extra options can be passed through the `ASAN_OPTIONS` environment variable,
e.g. `ASAN_OPTIONS=detect_leaks=0`.

Requires the 32-bit `libasan` for the host compiler (provided by `gcc-multilib`
on Debian/Ubuntu).
