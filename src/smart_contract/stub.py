"""Локальная заглушка смарт-контракта.

Пишет записи в local_registry/auction_registry_stub.json
(папка игнорируется git, см. .gitignore).
Когда руководитель даст API — просто заполните .env и заглушка перестанет
использоваться (см. factory.py).
"""

import json
import logging
from pathlib import Path

from .interface import SmartContractClient

log = logging.getLogger(__name__)


class StubSmartContract(SmartContractClient):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def register_auction_result(
        self,
        *,
        auction_id: str,
        assignment_hash: str,
        winners: list[str],
        tasks: list[str],
        total_score: float,
        timestamp: int,
    ) -> dict:
        records = json.loads(self.path.read_text(encoding="utf-8"))
        record = {
            "auction_id": auction_id,
            "assignment_hash": assignment_hash,
            "winners": winners,
            "tasks": tasks,
            "total_score": total_score,
            "timestamp": timestamp,
            "tx_hash": "0xSTUB" + assignment_hash[2:10],
            "event": "AuctionRegistered",
        }
        records.append(record)
        self.path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log.info("[STUB] AuctionRegistered, registry size = %d", len(records))
        return record
