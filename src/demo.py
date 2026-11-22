"""Точка входа. Запуск: python -m src.demo

Сценарий для видео (≈20-30 с):
  1. Подключаются 3 робота и координатор.
  2. Координатор публикует auction/start со списком задач.
  3. Роботы публикуют ставки в auction/bids.
  4. Координатор запускает точный аукцион, печатает назначение.
  5. Считается SHA-256, вызывается смарт-контракт (по умолчанию — заглушка).
  6. В логе появляется событие AuctionRegistered.
"""

import logging
import time

from .config import Settings
from .coordinator import Coordinator
from .models import Task
from .mqtt_client import MqttBus
from .robot_agent import RobotAgent
from .smart_contract import make_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("demo")


def main() -> None:
    settings = Settings()

    tasks = {
        1: Task(id=1, name="T1"),
        2: Task(id=2, name="T2"),
        3: Task(id=3, name="T3"),
    }
    robots = {1: "R1", 2: "R2", 3: "R3"}

    # Матрица эффективностей: у каждого робота свой «профиль»,
    # поэтому назначение нетривиально.
    efficiencies = {
        1: {1: 9.0, 2: 4.0, 3: 2.0},
        2: {1: 3.0, 2: 8.0, 3: 5.0},
        3: {1: 6.0, 2: 6.5, 3: 7.5},
    }

    # 1) роботы
    buses = {}
    for rid in robots:
        bus = MqttBus(
            settings.mqtt_host,
            settings.mqtt_port,
            settings.mqtt_username,
            settings.mqtt_password,
            client_id=f"robot-{rid}",
        )
        try:
            bus.connect()
        except ConnectionRefusedError:
            log.error(
                "MQTT broker is not running on %s:%d — start mosquitto first.",
                settings.mqtt_host,
                settings.mqtt_port,
            )
            raise SystemExit(1)
        buses[rid] = bus
        time.sleep(0.2)

    # 2) агенты (подписываются на auction/start)
    _agents = [
        RobotAgent(rid, robots[rid], buses[rid], efficiencies[rid])
        for rid in robots
    ]

    # 3) координатор
    coord_bus = MqttBus(
        settings.mqtt_host,
        settings.mqtt_port,
        settings.mqtt_username,
        settings.mqtt_password,
        client_id="coordinator",
    )
    coord_bus.connect()
    time.sleep(0.3)

    sc = make_client(settings)
    coordinator = Coordinator(coord_bus, sc, robots, tasks, timeout=1.5)
    time.sleep(0.2)

    # 4) прогон
    result = coordinator.run()

    log.info("=== FINAL ===")
    log.info("auction_id  = %s", result.auction_id)
    log.info("total_score = %.3f", result.total_score)
    for a in result.assignments:
        log.info("  %s -> %s (%.3f)", a.robot_name, a.task_name, a.value)

    # 5) корректное завершение
    coord_bus.disconnect()
    for bus in buses.values():
        bus.disconnect()


if __name__ == "__main__":
    main()
