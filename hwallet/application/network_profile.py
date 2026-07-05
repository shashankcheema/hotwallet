from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


SUPPORTED_NETWORKS = {"testnet", "prod"}


@dataclass(frozen=True)
class HederaNetworkProfile:
    network: str
    operator_id: str | None = None
    operator_key: str | None = None
    node_account_id: str | None = None


def _require(value: str | None, field_name: str, network: str) -> str:
    if not value:
        raise EnvironmentError(f"{field_name} must be set for the {network} profile.")
    return value


def resolve_hedera_network_profile(
    environ: Mapping[str, str] | None = None,
    require_credentials: bool = True,
    require_node_account: bool = False,
) -> HederaNetworkProfile:
    values = environ or os.environ
    network = values.get("HEDERA_NETWORK", "testnet").strip().lower()
    if network not in SUPPORTED_NETWORKS:
        raise ValueError("HEDERA_NETWORK must be either 'testnet' or 'prod'.")

    prefix = "TESTNET" if network == "testnet" else "PROD"
    operator_id = values.get(f"{prefix}_OPERATOR_ID")
    operator_key = values.get(f"{prefix}_OPERATOR_KEY")
    if require_credentials:
        operator_id = _require(operator_id, f"{prefix}_OPERATOR_ID", network)
        operator_key = _require(operator_key, f"{prefix}_OPERATOR_KEY", network)

    node_account_id = values.get(f"{prefix}_NODE_ACCOUNT_ID")
    if require_node_account:
        node_account_id = _require(node_account_id, f"{prefix}_NODE_ACCOUNT_ID", network)

    return HederaNetworkProfile(
        network=network,
        operator_id=operator_id,
        operator_key=operator_key,
        node_account_id=node_account_id,
    )
