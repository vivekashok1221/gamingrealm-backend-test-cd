from typing import TypeVar
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from loguru import logger
from passlib.hash import argon2

from prisma.models import User
from prisma.partials import UserProfile
from src.backend.auth.sessions import AbstractSessionStorage
from src.backend.dependencies import get_sessions
from src.backend.models import UserInLogin, UserInSignup

router = APIRouter(prefix="/user")
COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 2592000 seconds (30 days)

T = TypeVar("T", UUID, UserProfile, str)


async def hash_password(password: str) -> str:
    """Returns hash of the password."""
    logger.trace("Creating password hash.")
    return argon2.using(rounds=4).hash(password)


async def check_password(password: str, hash_: str) -> bool:
    """Compares salted-hash against hash of user-inputted password."""
    logger.trace("Checking if the password hashes match.")
    return argon2.verify(password, hash_)


async def set_session(
    user_profile: UserProfile, sessions: AbstractSessionStorage, message: str
) -> dict[str, T]:
    """Creates session and sets cookie."""
    session = await sessions.create_session(UUID(user_profile.id))
    return {"session_id": session.id, "user": user_profile, "message": message}


@router.post("/signup")
async def signup(
    user_login: UserInSignup = Body(),
    sessions: AbstractSessionStorage = Depends(get_sessions),
) -> dict[str, T]:
    """Endpoint to sign up a user.

    Returns session id and user details except password if authentication is successful.
    """
    username = user_login.username
    password = user_login.password
    email = user_login.email

    user: User | None = await User.prisma().find_first(
        where={"OR": [{"username": username}, {"email": email}]}
    )
    if user is not None:
        logger.debug("Sign up attempted with username or email which already exists.")
        raise HTTPException(status_code=409, detail="The username or email already exists")

    user = await User.prisma().create(
        data={"username": username, "email": email, "password": await hash_password(password)}
    )
    user_profile = UserProfile(**user.dict(exclude={"password"}))
    response: dict[str, T] = await set_session(user_profile, sessions, message="Account created.")

    logger.info(
        f"Account {user_profile.username}({user_profile.id}) successfully created."
        f"\nSession {response['session_id']} successfully created"
    )
    return response


@router.post("/login")
async def login(
    user_login: UserInLogin,
    session_id: UUID | None = Header(default=None, alias="session-id"),
    sessions: AbstractSessionStorage = Depends(get_sessions),
) -> dict[str, T]:
    """Endpoint to authenticate a user. Validation is done on form data before querying DB.

    Returns session id and user details except password if authentication is successful.
    """
    username = user_login.username
    password = user_login.password

    user: User | None = await User.prisma().find_first(where={"username": username})

    if user is None or (not await check_password(password, user.password)):
        raise HTTPException(status_code=404, detail="The username or password is incorrect.")
    user_profile = UserProfile(**user.dict(exclude={"password"}))
    response: dict[str, T] = await set_session(
        user_profile, sessions, message="Successfully logged in."
    )

    if session_id is not None and session_id in sessions:  # Checking for duplicate session.
        await sessions.delete_session(session_id)
        logger.warning(f"Deleted session {session_id} since a new session has been created.")

    logger.info(
        f"Session {response['session_id']} successfully created"
        f" for {user_profile.username}({user_profile.id})."
    )
    return response
