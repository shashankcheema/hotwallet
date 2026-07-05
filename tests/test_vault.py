from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from hwallet.infrastructure.vault_crypto import decryptWallet, decryptWalletBytes, encryptWallet


MNEMONIC = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
PASSWORD = "Mypassword123!"
EXPECTED_PAYLOAD = {
    "version": 1,
    "kdf": {
        "name": "scrypt",
        "n": 16384,
        "r": 8,
        "p": 1,
        "key_bytes": 32,
    },
    "cipher": {
        "name": "AES-256-GCM",
        "salt": "AQEBAQEBAQEBAQEBAQEBAQ==",
        "iv": "AgICAgICAgICAgIC",
        "ciphertext": "XWLrCWb45fURQG1CTi1TlPgM46wnXOeWtAQlunRs6RN74wWEPDPz2nwQMBjiXr7acLq40DO+I3m1ZRkkacpMy1qUthvwFD2+UKSx2nIiV5jgPIUNAL16HT8+0OX0",
        "auth_tag": "z8Ygvzd+E13aGu02NsAUfA==",
    },
}


class VaultCryptoTests(unittest.TestCase):
    def test_encrypt_wallet_is_deterministic_with_fixed_primitives(self) -> None:
        with patch(
            "hwallet.infrastructure.vault_crypto.secrets.token_bytes",
            side_effect=[b"\x01" * 16, b"\x02" * 12],
        ):
            payload = encryptWallet(MNEMONIC, PASSWORD)

        self.assertEqual(json.loads(payload), EXPECTED_PAYLOAD)

    def test_decrypt_wallet_round_trip(self) -> None:
        with patch(
            "hwallet.infrastructure.vault_crypto.secrets.token_bytes",
            side_effect=[b"\x01" * 16, b"\x02" * 12],
        ):
            payload = encryptWallet(MNEMONIC, PASSWORD)

        self.assertEqual(decryptWallet(payload, PASSWORD), MNEMONIC)

    def test_decrypt_wallet_bytes_returns_mutable_buffer(self) -> None:
        with patch(
            "hwallet.infrastructure.vault_crypto.secrets.token_bytes",
            side_effect=[b"\x01" * 16, b"\x02" * 12],
        ):
            payload = encryptWallet(MNEMONIC, PASSWORD)

        plaintext_bytes = decryptWalletBytes(payload, PASSWORD)
        try:
            self.assertIsInstance(plaintext_bytes, bytearray)
            self.assertEqual(plaintext_bytes.decode("utf-8"), MNEMONIC)
        finally:
            for index in range(len(plaintext_bytes)):
                plaintext_bytes[index] = 0
