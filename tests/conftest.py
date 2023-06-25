import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from prisma import Prisma
from src.backend import app


# set the anyio backend for the entire test session
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio", {"use_uvloop": True}


@pytest.fixture(scope="session")
@pytest.mark.anyio
async def db():
    prisma = Prisma()
    await prisma.connect()
    yield prisma
    await prisma.disconnect()


@pytest.fixture(scope="session")
@pytest.mark.anyio
async def _lifespan_aware_app():
    async with LifespanManager(app.app) as mgr:
        yield mgr.app


@pytest.fixture(scope="session")
@pytest.mark.anyio
async def client(_lifespan_aware_app):
    async with AsyncClient(app=_lifespan_aware_app, base_url="http://testserver") as client:
        yield client
