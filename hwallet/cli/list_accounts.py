from __future__ import annotations

import argparse
import os

from hwallet.application.account_state import WalletStateManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List Hedera accounts from wallet_state.json")
    parser.add_argument(
        "--state-path",
        default=os.getenv("WALLET_STATE_PATH", "wallet_state.json"),
        help="Path to the JSON wallet state file.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manager = WalletStateManager(args.state_path)
    for account in manager.list_accounts():
        print(
            {
                "account_id": account.account_id,
                "nickname": account.nickname,
                "address_index": account.address_index,
                "public_alias": account.public_alias,
                "public_key_hex": account.public_key_hex,
            }
        )


if __name__ == "__main__":
    main()
