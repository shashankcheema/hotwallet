from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv
from hiero_sdk_python import AccountId

from hwallet.application.hedera_services import HederaSigningService
from hwallet.application.network_profile import resolve_hedera_network_profile


SIGNING_SERVICE = HederaSigningService()


def main() -> None:
    load_dotenv(find_dotenv(usecwd=True))
    payload = os.getenv("VAULT_PAYLOAD")
    password = os.getenv("VAULT_PASSWORD")
    sender_account_id_value = os.getenv("SENDER_ACCOUNT_ID")
    recipient_account_id_value = os.getenv("RECIPIENT_ACCOUNT_ID")
    tinybars_value = os.getenv("TRANSFER_TINYBARS")
    memo = os.getenv("TRANSFER_MEMO")

    if (
        not payload
        or not password
        or not sender_account_id_value
        or not recipient_account_id_value
        or not tinybars_value
        or memo is None
    ):
        raise EnvironmentError(
            "VAULT_PAYLOAD, VAULT_PASSWORD, SENDER_ACCOUNT_ID, RECIPIENT_ACCOUNT_ID, TRANSFER_TINYBARS, and TRANSFER_MEMO must be set in the environment or .env file."
        )

    sender_account_id = AccountId.from_string(sender_account_id_value)
    recipient_account_id = AccountId.from_string(recipient_account_id_value)
    tinybars = int(tinybars_value)
    profile = resolve_hedera_network_profile(require_credentials=False, require_node_account=True)
    node_account_id = AccountId.from_string(profile.node_account_id)

    temporary_key_buffer = SIGNING_SERVICE.load_key_buffer(payload, password)
    signed_transaction_bytes = SIGNING_SERVICE.build_signed_transfer(
        sender_account_id=sender_account_id,
        recipient_account_id=recipient_account_id,
        tinybars=tinybars,
        memo=memo,
        temporary_key_buffer=temporary_key_buffer,
        node_account_id=node_account_id,
    )
    print(signed_transaction_bytes.hex())


if __name__ == "__main__":
    main()
