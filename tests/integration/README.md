## Running the integration tests locally

Pre-requisites:
 - networking for the native-sim board (see README)
 - pytest

To run the current tests, you will need to export
 - TEST_DEVICE_ID
 - TEST_TENANT_TOKEN
 - TEST_AUTH_TOKEN

as these are used to connect to hosted Mender.

You will also need to run `git submodule update --init --recursive` to get
the parts from mender-server (there are also parts from mender-integration, but
as of now this is just some small logging parts etc., we should remove the dependency on
the integration repo).

Run the tests with `pytest -s --host hosted.mender.io` in the `tests/integration` directory.
