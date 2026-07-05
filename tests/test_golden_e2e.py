from __future__ import annotations

import unittest
from unittest.mock import patch

from bip_utils import Bip39SeedGenerator
from hiero_sdk_python import AccountId, TransactionId

from hwallet.application.hedera_services import HederaSigningService
from hwallet.domain.key_derivation import derive_ethereum_key, derive_solana_key, generate_mnemonic
from hwallet.infrastructure.vault_crypto import decryptWallet, encryptWallet


MNEMONIC = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
PASSWORD = "Mypassword123!"
EXPECTED_SIGNED_HEX = (
    "2aa8010a3e0a0d0a060880e2cfaa06120318e907120218031880c2d72f220208783206676f6c64656e72180a160a090a0318e90710f1c0010a090a0318ea0710f2c00112660a640a2010fcec8c5db29aeab62272a08be39b1ec75eba50624351fba9948ff5d3d78ecf1a403b08f40445ffdc849bca8286d36a43a68608c0dfe273fcc1ad907bbb600394b8d881322f6bcc1b8126553b283b6c3e34654320e4a3388f901ebb89cd7218410f"
)


class GoldenEndToEndTests(unittest.TestCase):
    def test_seed_to_signed_hex_pipeline(self) -> None:
        with patch(
            "hwallet.domain.key_derivation.secrets.token_bytes",
            return_value=b"\x00" * 16,
        ):
            mnemonic = generate_mnemonic(128)

        self.assertEqual(mnemonic, MNEMONIC)

        seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
        self.assertEqual(
            derive_ethereum_key(seed_bytes),
            "1ab42cc412b618bdea3a599e3c9bae199ebf030895b039e9db1e30dafb12b727",
        )
        self.assertEqual(
            derive_solana_key(seed_bytes),
            "286b4b30f808ed46e986e5536939c4177b61588ac4a3080d228cb47edd798164",
        )

        with patch(
            "hwallet.infrastructure.vault_crypto.secrets.token_bytes",
            side_effect=[b"\x01" * 16, b"\x02" * 12],
        ):
            payload = encryptWallet(mnemonic, PASSWORD)

        self.assertEqual(decryptWallet(payload, PASSWORD), mnemonic)

        signing_service = HederaSigningService()
        temporary_key_buffer = signing_service.load_key_buffer(payload, PASSWORD)
        fixed_tx_id = TransactionId.from_string("0.0.1001@1700000000.000000000")

        with patch("hwallet.application.hedera_services.TransactionId.generate", return_value=fixed_tx_id):
            signed_bytes = signing_service.build_signed_transfer(
                sender_account_id=AccountId.from_string("0.0.1001"),
                recipient_account_id=AccountId.from_string("0.0.1002"),
                tinybars=12345,
                memo="golden",
                temporary_key_buffer=temporary_key_buffer,
                node_account_id=AccountId.from_string("0.0.3"),
            )

        self.assertEqual(signed_bytes.hex(), EXPECTED_SIGNED_HEX)
        self.assertTrue(all(value == 0 for value in temporary_key_buffer))
