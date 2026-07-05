from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv

from hwallet.infrastructure.vault_crypto import decryptWallet, encryptWallet


def main() -> None:
    load_dotenv(find_dotenv(usecwd=True))
    seed_phrase = os.getenv("SEED_PHRASE")
    password = os.getenv("WALLET_PASSWORD")
    if not seed_phrase or not password:
        raise EnvironmentError(
            "SEED_PHRASE and WALLET_PASSWORD must be set in the environment or .env file."
        )

    payload = encryptWallet(seed_phrase, password)
    print(payload)
    print(decryptWallet(payload, password))


if __name__ == "__main__":
    main()
