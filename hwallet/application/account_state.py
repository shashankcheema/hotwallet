from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ManagedAccount:
    account_id: str
    nickname: str
    address_index: int
    public_alias: str | None = None
    public_key_hex: str | None = None


@dataclass
class WalletState:
    accounts: list[ManagedAccount] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> WalletState:
        accounts = [
            ManagedAccount(
                account_id=str(account["account_id"]),
                nickname=str(account["nickname"]),
                address_index=int(account["address_index"]),
                public_alias=account.get("public_alias") if isinstance(account, dict) else None,
                public_key_hex=account.get("public_key_hex") if isinstance(account, dict) else None,
            )
            for account in data.get("accounts", [])
            if isinstance(account, dict)
        ]
        return cls(accounts=accounts)

    def to_dict(self) -> dict[str, object]:
        return {
            "version": 1,
            "accounts": [
                {
                    "account_id": account.account_id,
                    "nickname": account.nickname,
                    "address_index": account.address_index,
                    **({"public_alias": account.public_alias} if account.public_alias else {}),
                    **({"public_key_hex": account.public_key_hex} if account.public_key_hex else {}),
                }
                for account in self.accounts
            ],
        }


class WalletStateManager:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> WalletState:
        if not self.path.exists():
            return WalletState()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return WalletState.from_dict(data)

    def save(self, state: WalletState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def list_accounts(self) -> list[ManagedAccount]:
        return self.load().accounts

    def next_address_index(self) -> int:
        accounts = self.list_accounts()
        return 0 if not accounts else max(account.address_index for account in accounts) + 1

    def find_by_account_id(self, account_id: str) -> ManagedAccount | None:
        for account in self.list_accounts():
            if account.account_id == account_id:
                return account
        return None

    def resolve_address_index(self, account_id: str, default: int = 0) -> int:
        account = self.find_by_account_id(account_id)
        return account.address_index if account else default

    def register_account(
        self,
        account_id: str,
        nickname: str,
        public_alias: str | None = None,
        public_key_hex: str | None = None,
        address_index: int | None = None,
    ) -> ManagedAccount:
        state = self.load()
        account_index = self.next_address_index() if address_index is None else address_index
        updated_accounts = [account for account in state.accounts if account.account_id != account_id]
        managed_account = ManagedAccount(
            account_id=account_id,
            nickname=nickname,
            address_index=account_index,
            public_alias=public_alias,
            public_key_hex=public_key_hex,
        )
        updated_accounts.append(managed_account)
        state.accounts = sorted(updated_accounts, key=lambda account: account.address_index)
        self.save(state)
        return managed_account
