from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from prisma import Prisma
from src.backend.routers import post, user,tags

app = FastAPI(title="GamingRealm")
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


@app.on_event("startup")
async def connect_db() -> None:
    """Connects to the prisma query engine before app starts."""
    await db.connect()


@app.on_event("shutdown")
async def disconnect_db() -> None:
    """Clean up connections when the server shuts down."""
    await db.disconnect()


@app.get("/ping")
async def ping() -> dict[str, str]:
    """API Ping endpoint."""
    return {"message": "Pong!"}
