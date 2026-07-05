from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from hiero_sdk_python import Client


@runtime_checkable
class NetworkClientWrapper(Protocol):
    client: Client

    def close(self) -> None: ...


@dataclass
class HederaNetworkClient:
    client: Client

    def close(self) -> None:
        self.client.close()
