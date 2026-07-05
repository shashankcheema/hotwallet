from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from hwallet.application.network_client import HederaNetworkClient


class NetworkClientTests(unittest.TestCase):
    def test_close_delegates_to_sdk_client(self) -> None:
        sdk_client = MagicMock()
        wrapper = HederaNetworkClient(client=sdk_client)

        wrapper.close()

        sdk_client.close.assert_called_once()
