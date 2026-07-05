from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv

from hwallet.application.hedera_services import HederaExecutionService


EXECUTION_SERVICE = HederaExecutionService()


def main() -> None:
    load_dotenv(find_dotenv(usecwd=True))
    signed_transaction_hex = os.getenv("SIGNED_TRANSACTION_HEX")
    operator_id_value = os.getenv("OPERATOR_ID")
    operator_key_value = os.getenv("OPERATOR_KEY")

    if not signed_transaction_hex:
        raise EnvironmentError("SIGNED_TRANSACTION_HEX must be set in the environment or .env file.")
    if not operator_id_value or not operator_key_value:
        raise EnvironmentError("OPERATOR_ID and OPERATOR_KEY must be set in the environment or .env file.")

    client = EXECUTION_SERVICE.create_client(operator_id_value, operator_key_value)
    try:
        result = EXECUTION_SERVICE.execute_signed_hex(signed_transaction_hex, client)
        print(f"Status: {result.status}")
        print("Success: true")
    finally:
        client.close()


if __name__ == "__main__":
    main()
