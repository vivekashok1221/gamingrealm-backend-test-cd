from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from prisma import Prisma
from src.backend.routers import post, tags, user


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Lifespan handler that runs on app startup and shutdown."""
    # Connect to the prisma query engine before app starts.
    await db.connect()

    yield
    # Clean up connections when the server shuts down.
    await db.disconnect()


app = FastAPI(title="GamingRealm", lifespan=lifespan)
db = Prisma(auto_register=True)
app.include_router(user.router)
app.include_router(post.router)
app.include_router(tags.router)

# Allow all origins, all headers except Authorization and all request methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
async def ping() -> dict[str, str]:
    """API Ping endpoint."""
    return {"message": "Poooooong!"}
