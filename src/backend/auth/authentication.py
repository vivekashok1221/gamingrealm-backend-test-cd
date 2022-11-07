from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from passlib.hash import argon2
from prisma.models import User

from src.backend.auth.sessions import AbstractSessionStorage
from src.backend.dependencies import (
    get_sessions,
    validate_email,
    validate_password,
    validate_username,
)

router = APIRouter()
COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 2592000 seconds (30 days)


async def hash_password(password: str) -> str:
    """Returns hash of the password."""
    return argon2.using(rounds=4).hash(password)


async def check_password(password: str, hash_: str) -> bool:
    """Compares salted-hash against hash of user-inputted password."""
    return argon2.verify(password, hash_)


async def set_cookie(user: User, sessions: AbstractSessionStorage, message: str) -> JSONResponse:
    """Creates session and sets cookie."""
    session = await sessions.create_session(user.id)
    response = JSONResponse(status_code=200, content=message)
    response.set_cookie(
        key="session-id", value=session.id, secure=True, max_age=COOKIE_MAX_AGE, httponly=True
    )
    return response


@router.post("/signup")
async def signup(
    username: str = Depends(validate_username),
    password: str = Depends(validate_password),
    email: str = Depends(validate_email),
    sessions: AbstractSessionStorage = Depends(get_sessions),
) -> JSONResponse:
    """Endpoint to sign up a user.

    Returns a cookie with session id if authentication is successful.
    """
    user: User | None = await User.prisma().find_first(
        where={"OR": [{"username": username}, {"email": email}]}
    )
    if user is not None:
        raise HTTPException(status_code=409, detail="The username or email already exists")

    user = await User.prisma().create(
        data={"username": username, "email": email, "password": await hash_password(password)}
    )
    response = await set_cookie(user, sessions, message="Account created.")
    return response


@router.post("/login")
async def login(
    username: str = Depends(validate_username),
    password: str = Depends(validate_password),
    sessions: AbstractSessionStorage = Depends(get_sessions),
) -> JSONResponse:
    """Endpoint to authenticate a user. Validation is done on form data before querying DB.

    Returns a cookie with session id if authentication is successful.
    """
    user: User = await User.prisma().find_first(where={"username": username})

    if user is None or (not await check_password(password, user.password)):
        raise HTTPException(status_code=404, detail="The username or password is incorrect.")

    response = await set_cookie(user, sessions, message="Successfully logged in.")
    return response
