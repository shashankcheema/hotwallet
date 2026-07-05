from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


class CliTests(unittest.TestCase):
    def test_wallet_keys_main_prints_three_lines(self) -> None:
        from hwallet.cli import wallet_keys

        with patch.object(wallet_keys, "generate_mnemonic", return_value="mnemonic"), patch.object(
            wallet_keys, "Bip39SeedGenerator"
        ) as seed_generator, patch.object(wallet_keys, "derive_ethereum_key", return_value="eth"), patch.object(
            wallet_keys, "derive_solana_key", return_value="sol"
        ), patch("builtins.print") as print_mock:
            seed_generator.return_value.Generate.return_value = b"seed"
            wallet_keys.main()

        print_mock.assert_any_call("Generated Mnemonic: mnemonic")
        print_mock.assert_any_call("Derived Ethereum Private Key: eth")
        print_mock.assert_any_call("Derived Solana Private Key: sol")

    def test_wallet_vault_main_uses_env_and_prints_round_trip(self) -> None:
        from hwallet.cli import wallet_vault

        with patch.dict(os.environ, {"SEED_PHRASE": "seed", "WALLET_PASSWORD": "pass"}, clear=True), patch.object(
            wallet_vault, "encryptWallet", return_value="payload"
        ), patch.object(wallet_vault, "decryptWalletBytes", return_value=bytearray(b"seed")), patch.object(
            wallet_vault, "load_dotenv"
        ), patch.object(wallet_vault, "find_dotenv", return_value=""), patch("builtins.print") as print_mock:
            wallet_vault.main()

        print_mock.assert_any_call("payload")
        print_mock.assert_any_call("seed")

    def test_register_account_main_writes_state(self) -> None:
        from hwallet.cli import register_account

        with patch.object(register_account, "WalletStateManager") as manager_cls, patch(
            "sys.argv",
            [
                "register-account",
                "--account-id",
                "0.0.1001",
                "--nickname",
                "treasury",
                "--public-alias",
                "main-treasury",
                "--state-path",
                "wallet_state.json",
            ],
        ), patch("builtins.print") as print_mock:
            manager = MagicMock()
            manager.path = "wallet_state.json"
            manager.register_account.return_value = SimpleNamespace(
                account_id="0.0.1001",
                nickname="treasury",
                address_index=0,
                public_alias="main-treasury",
                public_key_hex=None,
            )
            manager_cls.return_value = manager
            register_account.main()

        manager.register_account.assert_called_once_with(
            account_id="0.0.1001",
            nickname="treasury",
            public_alias="main-treasury",
            public_key_hex=None,
            address_index=None,
        )
        print_mock.assert_called_once()

    def test_list_accounts_main_prints_accounts(self) -> None:
        from hwallet.cli import list_accounts

        with patch.object(list_accounts, "WalletStateManager") as manager_cls, patch(
            "sys.argv",
            ["list-accounts", "--state-path", "wallet_state.json"],
        ), patch("builtins.print") as print_mock:
            manager = MagicMock()
            manager.list_accounts.return_value = [
                SimpleNamespace(
                    account_id="0.0.1001",
                    nickname="treasury",
                    address_index=0,
                    public_alias="main-treasury",
                    public_key_hex=None,
                ),
                SimpleNamespace(
                    account_id="0.0.1002",
                    nickname="ops",
                    address_index=1,
                    public_alias="ops-wallet",
                    public_key_hex="abcd",
                ),
            ]
            manager_cls.return_value = manager
            list_accounts.main()

        self.assertEqual(print_mock.call_count, 2)
        manager.list_accounts.assert_called_once_with()

    def test_hedera_signer_main_prints_signed_hex(self) -> None:
        from hwallet.cli import hedera_signer

        fake_service = MagicMock()
        fake_service.load_key_buffer.return_value = bytearray(b"key")
        fake_service.build_signed_transfer.return_value = b"signed"

        with patch.dict(
            os.environ,
            {
                "VAULT_PAYLOAD": "payload",
                "VAULT_PASSWORD": "pass",
                "SENDER_ACCOUNT_ID": "0.0.1001",
                "RECIPIENT_ACCOUNT_ID": "0.0.1002",
                "TRANSFER_TINYBARS": "12345",
                "TRANSFER_MEMO": "memo",
            },
            clear=True,
        ), patch.object(hedera_signer, "SIGNING_SERVICE", fake_service), patch.object(
            hedera_signer, "AccountId"
        ) as account_id, patch.object(hedera_signer, "load_dotenv"), patch.object(
            hedera_signer, "find_dotenv", return_value=""
        ), patch.object(
            hedera_signer,
            "resolve_hedera_network_profile",
            return_value=SimpleNamespace(network="testnet", node_account_id="0.0.3"),
        ), patch.object(
            hedera_signer,
            "WalletStateManager",
        ) as wallet_state_manager_cls, patch("builtins.print") as print_mock:
            account_id.from_string.side_effect = lambda value: value
            wallet_state_manager_cls.return_value.resolve_address_index.return_value = 1
            hedera_signer.main()

        print_mock.assert_called_once_with("7369676e6564")

    def test_hedera_executor_main_prints_status(self) -> None:
        from hwallet.cli import hedera_executor

        fake_sdk_client = SimpleNamespace(close=MagicMock())
        fake_client = SimpleNamespace(client=fake_sdk_client, close=fake_sdk_client.close)
        fake_service = MagicMock()
        fake_service.create_client.return_value = fake_client
        fake_service.execute_signed_hex.return_value = SimpleNamespace(status="SUCCESS")

        with patch.dict(
            os.environ,
            {
                "SIGNED_TRANSACTION_HEX": "00ff",
            },
            clear=True,
        ), patch.object(hedera_executor, "EXECUTION_SERVICE", fake_service), patch.object(
            hedera_executor, "load_dotenv"
        ), patch.object(hedera_executor, "find_dotenv", return_value=""), patch.object(
            hedera_executor,
            "resolve_hedera_network_profile",
            return_value=SimpleNamespace(network="testnet", operator_id="0.0.123", operator_key="operator-key"),
        ), patch("builtins.print") as print_mock:
            hedera_executor.main()

        print_mock.assert_any_call("Status: SUCCESS")
        print_mock.assert_any_call("Success: true")
        fake_client.close.assert_called_once()
