from src.backend.auth.sessions import AbstractSessionStorage, InMemorySessionStorage

sessions = InMemorySessionStorage()


async def get_sessions() -> AbstractSessionStorage:
    """Returns session storage objects."""
    return sessions
