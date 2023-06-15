import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from src.backend import app


# set the anyio backend for the entire test session
@pytest.fixture
def anyio_backend():
    return "asyncio", {"use_uvloop": True}


@pytest.fixture(scope="session")
@pytest.mark.anyio
async def client() -> AsyncClient:
    async with LifespanManager(app.app) as _:
        async with AsyncClient(app=app.app) as client:
            return client
