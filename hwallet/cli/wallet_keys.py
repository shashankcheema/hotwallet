from __future__ import annotations

from bip_utils import Bip39SeedGenerator

from hwallet.domain.key_derivation import (
    derive_ethereum_key,
    derive_solana_key,
    generate_mnemonic,
)


def main() -> None:
    mnemonic = generate_mnemonic(entropy_bits=128)
    print(f"Generated Mnemonic: {mnemonic}")

    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    eth_private_key = derive_ethereum_key(seed_bytes)
    print(f"Derived Ethereum Private Key: {eth_private_key}")

    sol_private_key = derive_solana_key(seed_bytes)
    print(f"Derived Solana Private Key: {sol_private_key}")


if __name__ == "__main__":
    main()
