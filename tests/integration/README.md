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
 - TEST_TENANT_TOKEN
 - TEST_AUTH_TOKEN

as these are used to connect to hosted Mender.

Run `git submodule update --init --recursive`.

Run the tests with `pytest -s --host hosted.mender.io` in the `tests/integration` directory.
