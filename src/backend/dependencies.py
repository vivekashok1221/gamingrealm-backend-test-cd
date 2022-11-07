from fastapi import Form

from src.backend.auth.sessions import AbstractSessionStorage, InMemorySessionStorage

USERNAME_RE = "^[A-Za-z0-9_-]*$"
sessions = InMemorySessionStorage()


async def validate_username(username: str = Form(min_length=1, regex=USERNAME_RE)) -> str:
    """Returns username if it only contains alphanumeric characters, dashes or underscores."""
    return username


async def validate_password(password: str = Form(min_length=6)) -> str:
    """Validates that the password is over  5 characters and returns it."""
    return password


async def validate_email(email: str = Form()) -> str:
    """Validates email."""
    # TODO: add logic for validating email address
    return email


async def get_sessions() -> AbstractSessionStorage:
    """Returns session storage objects."""
    return sessions
