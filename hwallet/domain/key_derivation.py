import secrets

from bip_utils import (
    Bip39MnemonicGenerator,
    Bip39SeedGenerator,
    Bip44,
    Bip44Changes,
    Bip44Coins,
)


def generate_entropy(bits: int) -> bytes:
    if bits not in [128, 256]:
        raise ValueError("Use 128 bits for 12 words or 256 bits for 24 words.")
    return secrets.token_bytes(bits // 8)


def generate_mnemonic(entropy_bits: int = 128) -> str:
    entropy = generate_entropy(entropy_bits)
    mnemonic = Bip39MnemonicGenerator().FromEntropy(entropy)
    return mnemonic.ToStr()


def derive_ethereum_key(seed_bytes: bytes) -> str:
    wallet = (
        Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
        .Purpose()
        .Coin()
        .Account(0)
        .Change(Bip44Changes.CHAIN_EXT)
        .AddressIndex(0)
    )
    return wallet.PrivateKey().Raw().ToHex()


def derive_solana_key(seed_bytes: bytes) -> str:
    wallet = (
        Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)
        .Purpose()
        .Coin()
        .Account(0)
        .Change(Bip44Changes.CHAIN_EXT)
        .AddressIndex(0)
    )
    return wallet.PrivateKey().Raw().ToHex()

