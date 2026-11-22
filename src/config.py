"""Загрузка настроек из .env. Файл .env.example уже лежит в корне репозитория."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    mqtt_host: str = os.getenv("MQTT_HOST", "localhost")
    mqtt_port: int = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_username: str = os.getenv("MQTT_USERNAME", "")
    mqtt_password: str = os.getenv("MQTT_PASSWORD", "")

    sc_api_url: str = os.getenv("SMART_CONTRACT_API_URL", "")
    sc_address: str = os.getenv("SMART_CONTRACT_ADDRESS", "")
    sc_chain_id: str = os.getenv("SMART_CONTRACT_CHAIN_ID", "")
    sc_api_token: str = os.getenv("SMART_CONTRACT_API_TOKEN", "")

    @property
    def use_stub(self) -> bool:
        """Если URL API не задан — используем локальную заглушку."""
        return not self.sc_api_url

    @property
    def stub_path(self) -> Path:
        return Path("local_registry") / "auction_registry_stub.json"
