from fastapi import FastAPI

app = FastAPI(title="GamingRealm")


@app.get("/ping")
async def ping() -> dict[str, str]:
    """API Ping endpoint."""
    return {"message": "Pong!"}
