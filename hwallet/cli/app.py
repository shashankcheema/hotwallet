from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

import click
from bip_utils import Bip39SeedGenerator
from hiero_sdk_python import AccountId

from hwallet.application.account_state import ManagedAccount, WalletStateManager
from hwallet.application.hedera_services import HederaExecutionService, HederaSigningService
from hwallet.application.network_profile import resolve_hedera_network_profile
from hwallet.domain.key_derivation import derive_hedera_ed25519_key, generate_mnemonic
from hwallet.infrastructure.mirror_node import MirrorNodeClient
from hwallet.infrastructure.vault_crypto import encryptVault


SIGNING_SERVICE = HederaSigningService()
EXECUTION_SERVICE = HederaExecutionService()


def _default_vault_path() -> str:
    return os.getenv("WALLET_VAULT_PATH", "vault.json")


def _default_state_path() -> str:
    return os.getenv("WALLET_STATE_PATH", "wallet_state.json")


def _zeroize(buffer: bytearray) -> None:
    for index in range(len(buffer)):
        buffer[index] = 0


def _read_vault_payload(vault_path: str | Path) -> str:
    return Path(vault_path).read_text(encoding="utf-8")


def _write_vault_payload(vault_path: str | Path, payload: str) -> None:
    vault_file = Path(vault_path)
    vault_file.parent.mkdir(parents=True, exist_ok=True)
    vault_file.write_text(payload, encoding="utf-8")


def _resolve_account(manager: WalletStateManager, account_id: str | None) -> ManagedAccount:
    accounts = manager.list_accounts()
    if account_id:
        account = manager.find_by_account_id(account_id)
        if account is None:
            raise click.ClickException(f"Unknown account ID: {account_id}")
        return account
    if not accounts:
        raise click.ClickException("No accounts are registered in wallet_state.json.")
    if len(accounts) == 1:
        return accounts[0]

    choices = [account.account_id for account in accounts]
    selected_account_id = click.prompt("Select account ID", type=click.Choice(choices, case_sensitive=True))
    account = manager.find_by_account_id(selected_account_id)
    if account is None:
        raise click.ClickException(f"Unknown account ID: {selected_account_id}")
    return account


def _format_hbar(tinybars: int) -> str:
    return f"{Decimal(tinybars) / Decimal(100_000_000):f} HBAR"


def _format_transaction_id(value: object) -> str:
    if value is None:
        return "unknown"
    if hasattr(value, "to_string"):
        return str(value.to_string())
    return str(value)


@click.group()
def cli() -> None:
    """Interactive wallet CLI."""


@cli.command()
@click.option("--vault-path", default=_default_vault_path, show_default=True)
@click.option("--state-path", default=_default_state_path, show_default=True)
@click.option("--account-id", prompt="Hedera account ID")
@click.option("--nickname", prompt="Account nickname")
@click.option("--public-alias", default=None, show_default=False)
def init(vault_path: str, state_path: str, account_id: str, nickname: str, public_alias: str | None) -> None:
    """Create a new vault and register the first account."""
    passphrase = click.prompt("Vault passphrase", hide_input=True, confirmation_prompt=True)
    mnemonic = generate_mnemonic(entropy_bits=128)
    seed_buffer = bytearray(Bip39SeedGenerator(mnemonic).Generate())
    derive_hedera_ed25519_key(bytes(seed_buffer), address_index=0)
    _zeroize(seed_buffer)

    vault_payload = encryptVault(mnemonic, passphrase)
    _write_vault_payload(vault_path, vault_payload)

    state_manager = WalletStateManager(state_path)
    account = state_manager.register_account(
        account_id=account_id,
        nickname=nickname,
        public_alias=public_alias,
        address_index=0,
    )

    click.echo(f"Vault saved to {vault_path}")
    click.echo(f"State saved to {state_path}")
    click.echo(f"Mnemonic: {mnemonic}")
    click.echo(
        {
            "account_id": account.account_id,
            "nickname": account.nickname,
            "address_index": account.address_index,
            "public_alias": account.public_alias,
        }
    )


@cli.command()
@click.option("--account-id", default=None, help="Account ID to query.")
@click.option("--state-path", default=_default_state_path, show_default=True)
def balance(account_id: str | None, state_path: str) -> None:
    """Show HBAR and token balances."""
    profile = resolve_hedera_network_profile(require_credentials=False, require_node_account=False)
    state_manager = WalletStateManager(state_path)
    account = _resolve_account(state_manager, account_id)
    mirror_node = MirrorNodeClient(profile.network)
    snapshot = mirror_node.get_account_snapshot(account.account_id)

    click.echo(f"Account: {snapshot.account_id}")
    click.echo(f"Nickname: {account.nickname}")
    click.echo(f"HBAR: {_format_hbar(snapshot.hbar_balance_tinybars)}")
    if snapshot.token_balances:
        click.echo("Tokens:")
        for token_balance in snapshot.token_balances:
            click.echo(
                f"  - {token_balance['token_id']}: {token_balance['balance']}"
            )
    else:
        click.echo("Tokens: none")


@cli.command()
@click.option("--to", "recipient_account_id", prompt="Recipient account ID")
@click.option("--amount", type=float, prompt="HBAR amount")
@click.option("--memo", default="", show_default=False)
@click.option("--from-account", "sender_account_id", default=None, help="Source account ID.")
@click.option("--vault-path", default=_default_vault_path, show_default=True)
@click.option("--state-path", default=_default_state_path, show_default=True)
def transfer(
    recipient_account_id: str,
    amount: float,
    memo: str,
    sender_account_id: str | None,
    vault_path: str,
    state_path: str,
) -> None:
    """Sign, broadcast, and report a transfer."""
    profile = resolve_hedera_network_profile(require_credentials=True, require_node_account=True)
    state_manager = WalletStateManager(state_path)
    sender_account = _resolve_account(state_manager, sender_account_id)
    recipient = AccountId.from_string(recipient_account_id)
    sender = AccountId.from_string(sender_account.account_id)
    tinybars = int(Decimal(str(amount)) * Decimal(100_000_000))
    passphrase = click.prompt("Vault passphrase", hide_input=True)
    vault_payload = _read_vault_payload(vault_path)
    temporary_key_buffer = SIGNING_SERVICE.load_key_buffer(
        vault_payload,
        passphrase,
        address_index=sender_account.address_index,
    )
    try:
        node_account_id = AccountId.from_string(profile.node_account_id)
        signed_transaction_bytes = SIGNING_SERVICE.build_signed_transfer(
            sender_account_id=sender,
            recipient_account_id=recipient,
            tinybars=tinybars,
            memo=memo,
            temporary_key_buffer=temporary_key_buffer,
            node_account_id=node_account_id,
        )
        client = EXECUTION_SERVICE.create_client(
            profile.network,
            profile.operator_id,
            profile.operator_key,
        )
        try:
            result = EXECUTION_SERVICE.execute_signed_hex(signed_transaction_bytes.hex(), client)
        finally:
            client.close()
    finally:
        _zeroize(temporary_key_buffer)

    click.echo(f"Status: {result.status}")
    click.echo(f"Consensus transaction ID: {_format_transaction_id(result.receipt.transaction_id)}")


@cli.command()
@click.option("--account-id", default=None, help="Account ID to query.")
@click.option("--limit", default=10, show_default=True, type=int)
@click.option("--state-path", default=_default_state_path, show_default=True)
def history(account_id: str | None, limit: int, state_path: str) -> None:
    """Print recent on-chain activity."""
    profile = resolve_hedera_network_profile(require_credentials=False, require_node_account=False)
    state_manager = WalletStateManager(state_path)
    account = _resolve_account(state_manager, account_id)
    mirror_node = MirrorNodeClient(profile.network)
    transactions = mirror_node.get_transactions(account.account_id, limit=limit)

    click.echo(f"Account: {account.account_id} ({account.nickname})")
    for transaction in transactions:
        net_hbar = sum(
            transfer["amount"]
            for transfer in transaction.get("transfers", [])
            if transfer.get("account") == account.account_id
        )
        click.echo(
            {
                "timestamp": transaction.get("consensus_timestamp"),
                "transaction_id": transaction.get("transaction_id"),
                "name": transaction.get("name"),
                "result": transaction.get("result"),
                "net_hbar": _format_hbar(int(net_hbar)),
            }
        )


main = cli.main


if __name__ == "__main__":
    main()
