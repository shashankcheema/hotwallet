# Hot Wallet Project Notes

This file is the shared project reference. Keep it updated as implementation changes.

## Architecture
- `hwallet/domain/` contains pure wallet key-derivation logic.
- `hwallet/infrastructure/` contains the vault encryption and decryption adapter.
- `hwallet/application/` contains the Hedera signing and execution services.
- `hwallet/cli/` contains the runnable adapters and command entrypoints.

## Commands
Use either the installed Poetry scripts or `python -m` against the CLI modules:

- `wallet-keys` or `python -m hwallet.cli.wallet_keys`
- `wallet-vault` or `python -m hwallet.cli.wallet_vault`
- `hedera-signer` or `python -m hwallet.cli.hedera_signer`
- `hedera-executor` or `python -m hwallet.cli.hedera_executor`

## Step 1: Wallet Seed Generation

### Behavior
- `generate_entropy(bits)` accepts `128` or `256` and returns cryptographically random bytes.
- `generate_mnemonic(entropy_bits=128)` turns entropy into a BIP39 mnemonic.
- `derive_ethereum_key(seed_bytes)` derives the first Ethereum private key.
- `derive_solana_key(seed_bytes)` derives the first Solana private key.

### CLI Output
- A freshly generated mnemonic phrase.
- The derived Ethereum private key.
- The derived Solana private key.

## Step 2: Wallet Encryption Vault

### Behavior
- `encryptWallet(seed_phrase, password)` generates fresh salt and IV values, stretches the password with `scrypt`, encrypts with AES-256-GCM, and returns one JSON payload.
- `decryptWalletBytes(payload, password)` restores the seed phrase as mutable bytes so callers can zeroize the buffer after use.
- `decryptWallet(payload, password)` is the string-returning convenience wrapper.

### Security Notes
- Password bytes, derived key bytes, and plaintext buffers are zeroized after use where possible.
- `decryptWalletBytes()` is the preferred boundary for downstream cryptographic work.

## Step 3: Hedera Transaction Signing

### Behavior
- `HederaSigningService.load_key_buffer(payload, password)` decrypts the vault payload and derives a temporary Ed25519 signing buffer.
- `HederaSigningService.build_unsigned_transfer(...)` creates a transfer transaction, sets the memo, transaction ID, and node account, then freezes and serializes it.
- `HederaSigningService.sign_unsigned(...)` rehydrates the transaction from bytes, signs it, and returns the signed wire payload.
- `HederaSigningService.build_signed_transfer(...)` performs the full offline signing flow in one call.
- Hedera Ed25519 derivation uses a fully hardened path: `m/44'/3030'/0'/0'/0'`.
- `hwallet.application.network_client` defines the network-client wrapper protocol and adapter, so local tests can mock the full client boundary without touching testnet.

### Notes
- Transaction IDs are generated locally, so the host clock should stay in sync with network time.
- The signing service returns raw signed bytes only; it does not broadcast transactions.

## Step 4: Network Execution

### Behavior
- `HederaExecutionService.create_client(...)` creates a Hedera testnet client and applies operator credentials.
- `HederaExecutionService.rehydrate_tx_from_hex(...)` converts signed hex back into a transaction object.
- `HederaExecutionService.execute_signed_hex(...)` submits the transaction, fetches the receipt, and requires a success status.

### Failure Handling
- Precheck and receipt failures are surfaced as runtime errors.
- Ledger failures remain visible through the receipt status instead of being silently ignored.

## Environment
Runtime inputs are read from `.env` or the active environment by the CLI adapters.
