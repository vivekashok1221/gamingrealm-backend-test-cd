from uuid import UUID

from fastapi import APIRouter, Body, Cookie, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from passlib.hash import argon2
from prisma.models import User
from prisma.partials import UserProfile

from src.backend.auth.sessions import AbstractSessionStorage
from src.backend.dependencies import get_sessions
from src.backend.models import UserInLogin, UserInSignup

router = APIRouter(prefix="/user")
COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 2592000 seconds (30 days)


async def hash_password(password: str) -> str:
    """Returns hash of the password."""
    return argon2.using(rounds=4).hash(password)


async def check_password(password: str, hash_: str) -> bool:
    """Compares salted-hash against hash of user-inputted password."""
    return argon2.verify(password, hash_)


async def set_session(
    user_profile: UserProfile, sessions: AbstractSessionStorage, message: str
) -> dict:
    """Creates session and sets cookie."""
    session = await sessions.create_session(user_profile.id)
    return {"session_id": session.id, "user": user_profile.dict(), "message": message}


@router.post("/signup")
async def signup(
    user_login: UserInSignup = Body(),
    session_id: UUID = Cookie(),
    sessions: AbstractSessionStorage = Depends(get_sessions),
) -> JSONResponse:
    """Endpoint to sign up a user.

    Returns a username and session id if authentication is successful.
    """
    username = user_login.username
    password = user_login.password
    email = user_login.email

    user: User | None = await User.prisma().find_first(
        where={"OR": [{"username": username}, {"email": email}]}
    )
    if user is not None:
        raise HTTPException(status_code=409, detail="The username or email already exists")

    user = await User.prisma().create(
        data={"username": username, "email": email, "password": await hash_password(password)}
    )
    user_profile = UserProfile(user.dict(exclude={"password"}))
    response: dict = await set_session(user_profile, sessions, message="Account created.")
    return response


@router.post("/login")
async def login(
    user: UserInLogin,
    session_id: UUID | None = Header(default=None),
    sessions: AbstractSessionStorage = Depends(get_sessions),
) -> JSONResponse:
    """Endpoint to authenticate a user. Validation is done on form data before querying DB.

    Returns a cookie with session id if authentication is successful.
    """
    username = user.username
    password = user.password

    user: User = await User.prisma().find_first(where={"username": username})

    if user is None or (not await check_password(password, user.password)):
        raise HTTPException(status_code=404, detail="The username or password is incorrect.")
    user_profile = UserProfile(user.dict(exclude={"password"}))
    response = await set_session(user_profile, sessions, message="Successfully logged in.")
    return response
