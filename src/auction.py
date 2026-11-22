"""Аукцион: находит назначение, максимизирующее суммарную ставку.

Для N<=8 перебирает перестановки — этого достаточно для демо и это
математически точное решение той же задачи, что решают CBAA/CBBA/алг. 3.1.
"""

import itertools

from .models import Assignment, Bid, Task


def run_auction(
    bids: list[Bid],
    robots: dict[int, str],
    tasks: dict[int, Task],
) -> tuple[list[Assignment], float]:
    robot_ids = sorted(robots.keys())
    task_ids = sorted(tasks.keys())
    n, m = len(robot_ids), len(task_ids)
    if n == 0 or m == 0:
        return [], 0.0

    # Лучшая ставка по каждой паре (robot_id, task_id)
    value: dict[tuple[int, int], float] = {}
    for b in bids:
        key = (b.robot_id, b.task_id)
        if key not in value or b.value > value[key]:
            value[key] = b.value

    if n <= m:
        best_score, best_combo = -1.0, None
        for combo in itertools.permutations(range(m), n):
            s = sum(
                value.get((robot_ids[i], task_ids[j]), 0.0)
                for i, j in enumerate(combo)
            )
            if s > best_score:
                best_score, best_combo = s, combo
        assignments = []
        for i, j in enumerate(best_combo):
            rid, tid = robot_ids[i], task_ids[j]
            assignments.append(Assignment(
                robot_id=rid,
                robot_name=robots[rid],
                task_id=tid,
                task_name=tasks[tid].name,
                value=value.get((rid, tid), 0.0),
            ))
        return assignments, best_score

    # Роботов больше, чем задач: каждой задаче — ровно один робот
    best_score, best_combo = -1.0, None
    for combo in itertools.permutations(range(n), m):
        s = sum(
            value.get((robot_ids[j], task_ids[i]), 0.0)
            for i, j in enumerate(combo)
        )
        if s > best_score:
            best_score, best_combo = s, combo
    assignments = []
    for i, j in enumerate(best_combo):
        rid, tid = robot_ids[j], task_ids[i]
        assignments.append(Assignment(
            robot_id=rid,
            robot_name=robots[rid],
            task_id=tid,
            task_name=tasks[tid].name,
            value=value.get((rid, tid), 0.0),
        ))
    return assignments, best_score
