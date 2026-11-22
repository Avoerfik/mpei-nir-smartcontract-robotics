"""HTTP-клиент к реальному API смарт-контракта.

ВАЖНО: точную схему эндпоинтов и поля запроса уточните у руководителя.
Сейчас используется разумная заглушка:
  POST {SMART_CONTRACT_API_URL}/auctions
  Authorization: Bearer {SMART_CONTRACT_API_TOKEN}
"""

import logging

import requests

from .interface import SmartContractClient

log = logging.getLogger(__name__)


class HttpSmartContractClient(SmartContractClient):
    def __init__(self, base_url: str, address: str, chain_id: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.address = address
        self.chain_id = chain_id
        self.token = token

    def register_auction_result(
        self,
        *,
        auction_id,
        assignment_hash,
        winners,
        tasks,
        total_score,
        timestamp,
    ):
        url = f"{self.base_url}/auctions"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        payload = {
            "contract": self.address,
            "chain_id": self.chain_id,
            "auction_id": auction_id,
            "assignment_hash": assignment_hash,
            "winners": winners,
            "tasks": tasks,
            "total_score": total_score,
            "timestamp": timestamp,
        }
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        log.info("[HTTP] AuctionRegistered tx=%s", data.get("tx_hash", "?"))
        return data
