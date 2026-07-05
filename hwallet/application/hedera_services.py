from dataclasses import dataclass
from typing import Any

from bip_utils import Bip39SeedGenerator
from hiero_sdk_python import (
    AccountId,
    Client,
    PrivateKey,
    PrecheckError,
    ReceiptStatusError,
    ResponseCode,
    Transaction,
    TransactionId,
    TransactionReceipt,
    TransactionResponse,
    TransferTransaction,
)

from hwallet.infrastructure.vault_crypto import decryptWalletBytes
from hwallet.domain.key_derivation import derive_hedera_ed25519_key


DEFAULT_NODE_ACCOUNT_ID = AccountId.from_string("0.0.3")


def _zeroize(buffer: bytearray) -> None:
    for index in range(len(buffer)):
        buffer[index] = 0


def _coerce_bytes(value: bytes | bytearray | str) -> bytes:
    if isinstance(value, str):
        return bytes.fromhex(value.strip())
    return bytes(value)


@dataclass(frozen=True)
class ExecutionResult:
    transaction_hex: str
    status: ResponseCode | int
    success: bool
    receipt: TransactionReceipt


class HederaSigningService:
    def __init__(self, node_account_id: AccountId = DEFAULT_NODE_ACCOUNT_ID) -> None:
        self.node_account_id = node_account_id

    def load_key_buffer(
        self,
        payload: str | dict[str, Any],
        password: str,
    ) -> bytearray:
        plaintext_bytes = decryptWalletBytes(payload, password)
        try:
            seed_phrase = plaintext_bytes.decode("utf-8")
            seed_bytes = bytearray(Bip39SeedGenerator(seed_phrase).Generate())
            try:
                return bytearray(bytes.fromhex(derive_hedera_ed25519_key(bytes(seed_bytes))))
            finally:
                _zeroize(seed_bytes)
        finally:
            _zeroize(plaintext_bytes)

    def build_unsigned_transfer(
        self,
        sender_account_id: AccountId,
        recipient_account_id: AccountId,
        tinybars: int,
        memo: str,
        node_account_id: AccountId | None = None,
    ) -> bytes:
        transaction = TransferTransaction()
        transaction.add_hbar_transfer(sender_account_id, -tinybars)
        transaction.add_hbar_transfer(recipient_account_id, tinybars)
        transaction.set_transaction_memo(memo)
        transaction.set_node_account_id(node_account_id or self.node_account_id)
        transaction.set_transaction_id(TransactionId.generate(sender_account_id))
        return transaction.freeze().to_bytes()

    def sign_unsigned(
        self,
        unsigned_payload: bytes | bytearray | str,
        temporary_key_buffer: bytearray,
    ) -> bytes:
        transaction = Transaction.from_bytes(_coerce_bytes(unsigned_payload))
        signing_key = PrivateKey.from_bytes_ed25519(bytes(temporary_key_buffer))
        try:
            signed_transaction = transaction.freeze().sign(signing_key)
            return signed_transaction.to_bytes()
        finally:
            _zeroize(temporary_key_buffer)

    def build_signed_transfer(
        self,
        sender_account_id: AccountId,
        recipient_account_id: AccountId,
        tinybars: int,
        memo: str,
        temporary_key_buffer: bytearray,
        node_account_id: AccountId | None = None,
    ) -> bytes:
        unsigned_payload = self.build_unsigned_transfer(
            sender_account_id=sender_account_id,
            recipient_account_id=recipient_account_id,
            tinybars=tinybars,
            memo=memo,
            node_account_id=node_account_id,
        )
        return self.sign_unsigned(unsigned_payload, temporary_key_buffer)


class HederaExecutionService:
    def create_client(self, operator_id: str, operator_key: str) -> Client:
        client = Client.for_testnet()
        client.set_operator(
            AccountId.from_string(operator_id),
            PrivateKey.from_string(operator_key),
        )
        return client

    def rehydrate_tx_from_hex(self, signed_transaction_hex: str) -> Transaction:
        raw_bytes = bytes.fromhex(signed_transaction_hex.strip())
        return Transaction.from_bytes(raw_bytes)

    def _is_success_status(self, status: ResponseCode | int | Any) -> bool:
        return status == ResponseCode.SUCCESS or str(status) == str(ResponseCode.SUCCESS)

    def execute_signed_hex(
        self,
        signed_transaction_hex: str,
        client: Client,
    ) -> ExecutionResult:
        transaction = self.rehydrate_tx_from_hex(signed_transaction_hex)

        try:
            response = transaction.execute(client, wait_for_receipt=False)
        except PrecheckError as error:
            raise RuntimeError(f"Precheck failed: {error.status}") from error

        if not isinstance(response, TransactionResponse):
            raise RuntimeError("Unexpected execute() return type.")

        try:
            receipt = response.get_receipt(client)
        except ReceiptStatusError as error:
            raise RuntimeError(f"Receipt status failed: {error.status}") from error

        status = receipt.status
        if not self._is_success_status(status):
            raise RuntimeError(f"Transaction failed with status: {status}")

        return ExecutionResult(
            transaction_hex=signed_transaction_hex,
            status=status,
            success=True,
            receipt=receipt,
        )
