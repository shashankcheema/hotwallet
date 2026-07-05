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
    "2aa8010a3e0a0d0a060880e2cfaa06120318e907120218031880c2d72f220208783206676f6c64656e72180a160a090a0318e90710f1c0010a090a0318ea0710f2c00112660a640a20e96b1c6b8769fdb0b34fbecfdf85c33b053cecad9517e1ab88cba614335775c11a400de09cb9870a066c0899cb3cf046fa45fbef4c4549b0c6fe8ed182d1d4a91aa30cc9429dbbc8295a1e6fd3af37086887b4fb0172779f16ca3cecae4c22838c01"
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
