"""Координатор: собирает ставки, запускает аукцион, регистрирует результат."""

import itertools
import logging
import threading
import time
import uuid

from .auction import run_auction
from .hashing import compute_hash
from .models import Assignment, AuctionResult, Bid, Task
from .mqtt_client import MqttBus
from .smart_contract.interface import SmartContractClient

log = logging.getLogger(__name__)


class Coordinator:
    def __init__(
        self,
        bus: MqttBus,
        sc_client: SmartContractClient,
        robots: dict[int, str],
        tasks: dict[int, Task],
        timeout: float = 1.5,
    ) -> None:
        self.bus = bus
        self.sc = sc_client
        self.robots = robots
        self.tasks = tasks
        self.timeout = timeout
        self.bids: list[Bid] = []
        self._lock = threading.Lock()
        bus.subscribe("auction/bids", self._on_bid)

    def _on_bid(self, _topic: str, payload: dict) -> None:
        bid = Bid(
            robot_id=int(payload["robot_id"]),
            robot_name=str(payload["robot_name"]),
            task_id=int(payload["task_id"]),
            value=float(payload["value"]),
        )
        with self._lock:
            self.bids.append(bid)

    def _verify_optimality(
        self,
        assignments: list[Assignment],
        score: float,
        collected: list[Bid],
    ) -> None:
        """Сверяет результат аукциона с полным перебором — только для демо.

        Пропускается, если перебор был бы слишком дорогим или невозможным
        (N > M). Основной алгоритм в auction.run_auction от этого не зависит.
        """
        n_robots = len(self.robots)
        m_tasks = len(self.tasks)
        if n_robots == 0 or m_tasks == 0:
            return
        if n_robots > m_tasks:
            # run_auction в этом случае идёт по ветке "M из N",
            # и проверка ниже её не повторяет.
            return
        if n_robots > 6 or m_tasks > 6:
            # P(6,6)=720 — предел, выше перебор бессмысленно тормозит демо.
            return

        val = {(b.robot_id, b.task_id): b.value for b in collected}
        rids = sorted(self.robots)
        tids = sorted(self.tasks)
        brute = max(
            sum(val.get((rids[i], tids[j]), 0.0) for i, j in enumerate(p))
            for p in itertools.permutations(range(len(tids)), len(rids))
        )
        log.info("проверка: оптимум по перебору = %.3f", brute)
        assert abs(brute - score) < 1e-9, (
            f"аукцион вернул {score:.6f}, полный перебор даёт {brute:.6f}"
        )

    def run(self, auction_id: str | None = None) -> AuctionResult:
        auction_id = auction_id or f"auc-{uuid.uuid4().hex[:8]}"
        with self._lock:
            self.bids.clear()
        started_at = time.time()

        tasks_payload = [{"id": t.id, "name": t.name} for t in self.tasks.values()]
        log.info("auction %s start, tasks=%s",
                 auction_id, [t.name for t in self.tasks.values()])
        self.bus.publish("auction/start", {
            "auction_id": auction_id,
            "tasks": tasks_payload,
        })

        expected = len(self.robots) * len(self.tasks)
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            with self._lock:
                count = len(self.bids)
            if count >= expected:
                break
            time.sleep(0.05)
        with self._lock:
            collected = list(self.bids)
        log.info("collected %d/%d bids", len(collected), expected)

        assignments, score = run_auction(collected, self.robots, self.tasks)
        finished_at = time.time()

        result = AuctionResult(
            auction_id=auction_id,
            assignments=assignments,
            total_score=score,
            started_at=started_at,
            finished_at=finished_at,
        )

        log.info("auction result:")
        for a in assignments:
            log.info("  %s -> %s (value=%.3f)", a.robot_name, a.task_name, a.value)
        log.info("total_score = %.3f", score)

        # Демо-проверка ДО записи в смарт-контракт, чтобы при ошибке
        # ничего «неправильного» не ушло в реестр.
        self._verify_optimality(assignments, score, collected)

        h = compute_hash(result)
        log.info("assignment hash = %s", h)

        tx = self.sc.register_auction_result(
            auction_id=auction_id,
            assignment_hash=h,
            winners=[a.robot_name for a in assignments],
            tasks=[a.task_name for a in assignments],
            total_score=score,
            timestamp=int(finished_at),
        )
        log.info("smart-contract: %s", tx.get("event", "AuctionRegistered"))

        self.bus.publish("auction/result", {
            "auction_id": auction_id,
            "assignments": [
                {"robot": a.robot_name, "task": a.task_name, "value": a.value}
                for a in assignments
            ],
            "score": score,
            "hash": h,
        })
        return result
