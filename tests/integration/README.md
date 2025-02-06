## Running the integration tests locally

Pre-requisites:
 - networking for the native-sim board (see README)
 - pytest

To run the current tests, you will need to export
 - TEST_DEVICE_ID
 - TEST_TENANT_TOKEN
 - TEST_AUTH_TOKEN

as these are used to connect to hosted Mender.

Run `git submodule update --init --recursive`.

Run the tests with `pytest -s --host hosted.mender.io` in the `tests/integration` directory.
