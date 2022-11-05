from fastapi import FastAPI
from prisma import Prisma

app = FastAPI(title="GamingRealm")
db = Prisma(auto_register=True)


@app.on_event("shutdown")
async def disconnect_db() -> None:
    """Clean up connections when the server shuts down."""
    await db.disconnect()


@app.get("/ping")
async def ping() -> dict[str, str]:
    """API Ping endpoint."""
    return {"message": "Pong!"}
