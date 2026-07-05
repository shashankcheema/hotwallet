from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


NETWORK_BASE_URLS = {
    "testnet": "https://testnet.mirrornode.hedera.com",
    "prod": "https://mainnet.mirrornode.hedera.com",
}


@dataclass(frozen=True)
class AccountSnapshot:
    account_id: str
    hbar_balance_tinybars: int
    token_balances: list[dict[str, Any]]


class MirrorNodeError(RuntimeError):
    pass


class MirrorNodeClient:
    def __init__(self, network: str, timeout: float = 10.0) -> None:
        network_key = network.strip().lower()
        if network_key not in NETWORK_BASE_URLS:
            raise ValueError("network must be either 'testnet' or 'prod'.")
        self.base_url = NETWORK_BASE_URLS[network_key]
        self.timeout = timeout

    def _get_json(self, path: str, query: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.base_url + path
        if query:
            url += "?" + urlencode(query, doseq=True)
        request = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise MirrorNodeError(f"mirror node request failed ({error.code}): {path}") from error
        except URLError as error:
            raise MirrorNodeError(f"mirror node request failed: {error.reason}") from error

    def get_account(self, account_id: str) -> dict[str, Any]:
        return self._get_json(f"/api/v1/accounts/{account_id}")

    def get_account_snapshot(self, account_id: str) -> AccountSnapshot:
        account = self.get_account(account_id)
        balance = account.get("balance") or {}
        return AccountSnapshot(
            account_id=str(account.get("account", account_id)),
            hbar_balance_tinybars=int(balance.get("balance", 0)),
            token_balances=list(balance.get("tokens", [])),
        )

    def get_account_tokens(self, account_id: str) -> dict[str, Any]:
        return self._get_json(f"/api/v1/accounts/{account_id}/tokens")

    def get_token_info(self, token_id: str) -> dict[str, Any]:
        return self._get_json(f"/api/v1/tokens/{token_id}")

    def get_transactions(self, account_id: str, limit: int = 25) -> list[dict[str, Any]]:
        data = self._get_json(
            "/api/v1/transactions",
            query={"account.id": account_id, "limit": limit, "order": "desc"},
        )
        return list(data.get("transactions", []))
