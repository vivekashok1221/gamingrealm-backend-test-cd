from typing import Literal
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from loguru import logger

from src.backend.auth.sessions import AbstractSessionStorage, InMemorySessionStorage, Session

_sessions = InMemorySessionStorage()


async def get_sessions() -> AbstractSessionStorage:
    """Returns session storage object."""
    return _sessions


async def is_authorized(
    user_id: UUID | None = Header(default=None, alias="user-id"),
    session_id: UUID | None = Header(default=None, alias="session-id"),
    sessions: AbstractSessionStorage = Depends(get_sessions),
) -> Literal[True]:
    """The headers must include user-id and session-id."""
    logger.trace(f"Attempting authorization with session id: {session_id} and user id: {user_id}")
    if session_id is None or user_id is None:  # better type-narrowing than None in (session, user)
        raise HTTPException(status_code=400, detail="Missing required headers.")

    session: Session | None = await sessions.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=440, detail="Invalid session id or session has expired.")

    if user_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not Authorized.")

    return True
