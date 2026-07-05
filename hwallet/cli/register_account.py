from __future__ import annotations

import argparse
import os

from hwallet.application.account_state import WalletStateManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Register a Hedera account in wallet_state.json")
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--nickname", required=True)
    parser.add_argument("--public-alias")
    parser.add_argument("--public-key-hex")
    parser.add_argument("--address-index", type=int)
    parser.add_argument(
        "--state-path",
        default=os.getenv("WALLET_STATE_PATH", "wallet_state.json"),
        help="Path to the JSON wallet state file.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manager = WalletStateManager(args.state_path)
    account = manager.register_account(
        account_id=args.account_id,
        nickname=args.nickname,
        public_alias=args.public_alias,
        public_key_hex=args.public_key_hex,
        address_index=args.address_index,
    )
    print(
        {
            "account_id": account.account_id,
            "nickname": account.nickname,
            "address_index": account.address_index,
            "public_alias": account.public_alias,
            "public_key_hex": account.public_key_hex,
            "state_path": str(manager.path),
        }
    )


if __name__ == "__main__":
    main()
