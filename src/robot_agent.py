"""Робот-агент: получает auction/start и публикует ставки в auction/bids."""

import logging
import time

from .mqtt_client import MqttBus

log = logging.getLogger(__name__)


class RobotAgent:
    def __init__(
        self,
        robot_id: int,
        name: str,
        bus: MqttBus,
        efficiency: dict[int, float],
    ) -> None:
        self.robot_id = robot_id
        self.name = name
        self.bus = bus
        self.efficiency = efficiency
        bus.subscribe("auction/start", self._on_start)

    def _on_start(self, _topic: str, payload: dict) -> None:
        time.sleep(0.05 * self.robot_id)
        tasks = payload.get("tasks", [])
        log.info("[%s] received auction, tasks=%s", self.name, [t["name"] for t in tasks])
        for t in tasks:
            task_id = t["id"]
            value = float(self.efficiency.get(task_id, 0.0))
            self.bus.publish("auction/bids", {
                "robot_id": self.robot_id,
                "robot_name": self.name,
                "task_id": task_id,
                "value": value,
            })
            log.info("[%s] bid T%d = %.3f", self.name, task_id, value)
