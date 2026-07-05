from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hwallet.application.account_state import WalletStateManager


class AccountStateTests(unittest.TestCase):
    def test_register_and_reload_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "wallet_state.json"
            manager = WalletStateManager(state_path)

            first = manager.register_account(
                account_id="0.0.1001",
                nickname="treasury",
                public_alias="main-treasury",
            )
            second = manager.register_account(
                account_id="0.0.1002",
                nickname="ops",
                public_alias="ops-wallet",
            )

            self.assertEqual(first.address_index, 0)
            self.assertEqual(second.address_index, 1)
            self.assertEqual(manager.resolve_address_index("0.0.1002"), 1)
            self.assertEqual(manager.next_address_index(), 2)

            reloaded = manager.load()
            self.assertEqual(len(reloaded.accounts), 2)
            self.assertEqual(reloaded.accounts[0].nickname, "treasury")
            self.assertEqual(reloaded.accounts[1].public_alias, "ops-wallet")

            raw_json = state_path.read_text(encoding="utf-8")
            self.assertIn("main-treasury", raw_json)
            self.assertIn("ops-wallet", raw_json)
            self.assertNotIn("seed", raw_json.lower())
