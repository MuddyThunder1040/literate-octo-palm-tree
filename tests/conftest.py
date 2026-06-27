import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app_services.market_repository import market_repository


@pytest.fixture
def client():
    with patch.object(market_repository, "connect"), \
         patch.object(market_repository, "close"):
        import main
        with TestClient(main.app, raise_server_exceptions=True) as c:
            yield c
