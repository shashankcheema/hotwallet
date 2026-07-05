from __future__ import annotations

import unittest
from unittest.mock import patch

from bip_utils import Bip39SeedGenerator

from hwallet.domain.key_derivation import (
    derive_ethereum_key,
    derive_solana_key,
    generate_entropy,
    generate_mnemonic,
)


MNEMONIC = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
ETHEREUM_KEY = "1ab42cc412b618bdea3a599e3c9bae199ebf030895b039e9db1e30dafb12b727"
SOLANA_KEY = "286b4b30f808ed46e986e5536939c4177b61588ac4a3080d228cb47edd798164"


class DomainKeyDerivationTests(unittest.TestCase):
    def test_generate_entropy_accepts_supported_sizes(self) -> None:
        with patch("hwallet.domain.key_derivation.secrets.token_bytes", return_value=b"\xAA" * 16):
            self.assertEqual(generate_entropy(128), b"\xAA" * 16)

        with patch("hwallet.domain.key_derivation.secrets.token_bytes", return_value=b"\xBB" * 32):
            self.assertEqual(generate_entropy(256), b"\xBB" * 32)

    def test_generate_entropy_rejects_unsupported_sizes(self) -> None:
        with self.assertRaises(ValueError):
            generate_entropy(192)

    def test_generate_mnemonic_from_entropy(self) -> None:
        with patch(
            "hwallet.domain.key_derivation.generate_entropy",
            return_value=b"\x00" * 16,
        ):
            self.assertEqual(generate_mnemonic(128), MNEMONIC)

    def test_derive_ethereum_key(self) -> None:
        seed_bytes = Bip39SeedGenerator(MNEMONIC).Generate()
        self.assertEqual(derive_ethereum_key(seed_bytes), ETHEREUM_KEY)

    def test_derive_solana_key(self) -> None:
        seed_bytes = Bip39SeedGenerator(MNEMONIC).Generate()
        self.assertEqual(derive_solana_key(seed_bytes), SOLANA_KEY)
