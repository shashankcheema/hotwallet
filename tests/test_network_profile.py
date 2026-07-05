from __future__ import annotations

import unittest

from hwallet.application.network_profile import resolve_hedera_network_profile


class NetworkProfileTests(unittest.TestCase):
    def test_resolve_testnet_profile(self) -> None:
        profile = resolve_hedera_network_profile(
            {
                "HEDERA_NETWORK": "testnet",
                "TESTNET_OPERATOR_ID": "0.0.123",
                "TESTNET_OPERATOR_KEY": "key",
                "TESTNET_NODE_ACCOUNT_ID": "0.0.3",
            }
        )

        self.assertEqual(profile.network, "testnet")
        self.assertEqual(profile.operator_id, "0.0.123")
        self.assertEqual(profile.operator_key, "key")
        self.assertEqual(profile.node_account_id, "0.0.3")

    def test_resolve_prod_profile(self) -> None:
        profile = resolve_hedera_network_profile(
            {
                "HEDERA_NETWORK": "prod",
                "PROD_OPERATOR_ID": "0.0.456",
                "PROD_OPERATOR_KEY": "prod-key",
                "PROD_NODE_ACCOUNT_ID": "0.0.4",
            }
        )

        self.assertEqual(profile.network, "prod")
        self.assertEqual(profile.operator_id, "0.0.456")
        self.assertEqual(profile.operator_key, "prod-key")
        self.assertEqual(profile.node_account_id, "0.0.4")

    def test_rejects_invalid_network(self) -> None:
        with self.assertRaises(ValueError):
            resolve_hedera_network_profile({"HEDERA_NETWORK": "staging"})

    def test_requires_node_account_when_requested(self) -> None:
        with self.assertRaises(EnvironmentError):
            resolve_hedera_network_profile(
                {
                    "HEDERA_NETWORK": "testnet",
                    "TESTNET_OPERATOR_ID": "0.0.123",
                    "TESTNET_OPERATOR_KEY": "key",
                },
                require_node_account=True,
            )
