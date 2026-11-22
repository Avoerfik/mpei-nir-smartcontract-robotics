"""Простые dataclass-модели для обмена между модулями."""

import time
from dataclasses import dataclass, field


@dataclass
class Task:
    id: int
    name: str


@dataclass
class Bid:
    robot_id: int
    robot_name: str
    task_id: int
    value: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class Assignment:
    robot_id: int
    robot_name: str
    task_id: int
    task_name: str
    value: float


@dataclass
class AuctionResult:
    auction_id: str
    assignments: list[Assignment]
    total_score: float
    started_at: float
    finished_at: float
