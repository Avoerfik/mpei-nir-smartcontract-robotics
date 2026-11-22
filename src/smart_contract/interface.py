from abc import ABC, abstractmethod


class SmartContractClient(ABC):
    @abstractmethod
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
        """Регистрирует итог аукциона. Возвращает dict с полем 'event'."""
