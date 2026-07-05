from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from hiero_sdk_python import AccountId, ResponseCode, TransactionId

from hwallet.application.hedera_services import HederaExecutionService, HederaSigningService
from hwallet.infrastructure.vault_crypto import encryptWallet


MNEMONIC = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
PASSWORD = "Mypassword123!"


class HederaApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        with patch(
            "hwallet.infrastructure.vault_crypto.secrets.token_bytes",
            side_effect=[b"\x01" * 16, b"\x02" * 12],
        ):
            self.vault_payload = encryptWallet(MNEMONIC, PASSWORD)

    def test_load_key_buffer_returns_expected_bytes(self) -> None:
        service = HederaSigningService()
        key_buffer = service.load_key_buffer(self.vault_payload, PASSWORD)
        try:
            self.assertEqual(
                key_buffer.hex(),
                "523f9ff611ac02e8e188617750e7e50feabd2ef9ee9b218a5c8ce2693275361d",
            )
        finally:
            for index in range(len(key_buffer)):
                key_buffer[index] = 0

    def test_build_unsigned_transfer_serializes_transaction(self) -> None:
        service = HederaSigningService()
        fixed_tx_id = TransactionId.from_string("0.0.1001@1700000000.000000000")

        with patch("hwallet.application.hedera_services.TransactionId.generate", return_value=fixed_tx_id):
            unsigned_bytes = service.build_unsigned_transfer(
                sender_account_id=AccountId.from_string("0.0.1001"),
                recipient_account_id=AccountId.from_string("0.0.1002"),
                tinybars=12345,
                memo="golden",
            )

        self.assertIsInstance(unsigned_bytes, bytes)
        self.assertGreater(len(unsigned_bytes), 0)

    def test_sign_unsigned_zeroizes_temporary_buffer(self) -> None:
        service = HederaSigningService()
        fixed_tx_id = TransactionId.from_string("0.0.1001@1700000000.000000000")

        with patch("hwallet.application.hedera_services.TransactionId.generate", return_value=fixed_tx_id):
            unsigned_bytes = service.build_unsigned_transfer(
                sender_account_id=AccountId.from_string("0.0.1001"),
                recipient_account_id=AccountId.from_string("0.0.1002"),
                tinybars=12345,
                memo="golden",
            )

        temporary_key_buffer = service.load_key_buffer(self.vault_payload, PASSWORD)
        signed_bytes = service.sign_unsigned(unsigned_bytes, temporary_key_buffer)

        self.assertIsInstance(signed_bytes, bytes)
        self.assertGreater(len(signed_bytes), 0)
        self.assertTrue(all(value == 0 for value in temporary_key_buffer))

    def test_create_client_sets_operator(self) -> None:
        service = HederaExecutionService()
        fake_client = MagicMock()

        with patch("hwallet.application.hedera_services.Client.for_testnet", return_value=fake_client), patch(
            "hwallet.application.hedera_services.AccountId.from_string",
            return_value="account-id",
        ), patch("hwallet.application.hedera_services.PrivateKey.from_string", return_value="private-key"):
            client = service.create_client("0.0.123", "operator-key")

        self.assertIs(client, fake_client)
        fake_client.set_operator.assert_called_once_with("account-id", "private-key")

    def test_execute_signed_hex_success_path(self) -> None:
        service = HederaExecutionService()
        fake_transaction = MagicMock()
        fake_receipt = SimpleNamespace(status=ResponseCode.SUCCESS)
        fake_response = SimpleNamespace(get_receipt=MagicMock(return_value=fake_receipt))
        fake_transaction.execute.return_value = fake_response

        with patch.object(service, "rehydrate_tx_from_hex", return_value=fake_transaction), patch(
            "hwallet.application.hedera_services.TransactionResponse",
            SimpleNamespace,
        ):
            result = service.execute_signed_hex("00ff", client=object())

        self.assertTrue(result.success)
        self.assertEqual(result.status, ResponseCode.SUCCESS)
        fake_transaction.execute.assert_called_once()
        fake_response.get_receipt.assert_called_once()
