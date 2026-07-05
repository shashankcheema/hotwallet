from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv

from hwallet.application.hedera_services import HederaExecutionService
from hwallet.application.network_profile import resolve_hedera_network_profile


EXECUTION_SERVICE = HederaExecutionService()


def main() -> None:
    load_dotenv(find_dotenv(usecwd=True))
    signed_transaction_hex = os.getenv("SIGNED_TRANSACTION_HEX")

    if not signed_transaction_hex:
        raise EnvironmentError("SIGNED_TRANSACTION_HEX must be set in the environment or .env file.")

    profile = resolve_hedera_network_profile()
    client = EXECUTION_SERVICE.create_client(
        profile.network,
        profile.operator_id,
        profile.operator_key,
    )
    try:
        result = EXECUTION_SERVICE.execute_signed_hex(signed_transaction_hex, client)
        print(f"Status: {result.status}")
        print("Success: true")
    finally:
        client.close()


if __name__ == "__main__":
    main()
