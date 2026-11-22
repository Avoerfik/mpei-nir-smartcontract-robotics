from ..config import Settings
from .http_client import HttpSmartContractClient
from .interface import SmartContractClient
from .stub import StubSmartContract


def make_client(settings: Settings) -> SmartContractClient:
    if settings.use_stub:
        return StubSmartContract(settings.stub_path)
    return HttpSmartContractClient(
        base_url=settings.sc_api_url,
        address=settings.sc_address,
        chain_id=settings.sc_chain_id,
        token=settings.sc_api_token,
    )
