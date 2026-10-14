"""Offline HTTP fixture worker using the unchanged process controller and gate."""

import json

from mock_harness import MockHarness


class HttpFixtureHarness(MockHarness):
    # Trusted class selection, never a path or endpoint supplied in public JSON.
    _worker_file = 'http_fixture_worker.py'

    def __init__(self, manifest_json, expected_sha256, credentials):
        super().__init__(manifest_json, expected_sha256, credentials)
        from http_fixture_worker import validate_fixture

        for row in self._cases:
            if row['scenario'] != 'success':
                raise ValueError('HTTP fixtures require fixed worker mode')
            validate_fixture(json.loads(row['reply']))
