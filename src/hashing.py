"""Канонический SHA-256 от результата аукциона.

Одинаковый результат на любой машине даёт одинаковый хеш:
сортируем назначения по robot_id и округляем значения.
"""

import hashlib
import json

from .models import AuctionResult


def compute_hash(result: AuctionResult) -> str:
    payload = {
        "auction_id": result.auction_id,
        "assignments": [
            {
                "robot_id": a.robot_id,
                "task_id": a.task_id,
                "value": round(a.value, 6),
            }
            for a in sorted(result.assignments, key=lambda x: x.robot_id)
        ],
        "total_score": round(result.total_score, 6),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "0x" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
