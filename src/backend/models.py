import re

from prisma.partials import UserInLogin_
from pydantic import EmailStr, validator

USERNAME_RE = re.compile("^[A-Za-z0-9_-]*$")


class UserInLogin(UserInLogin_):
    """Model representing user at login."""

    @validator("username")
    def _validate_username(cls, username: str) -> str:
        """Checks if username only contains alphanumeric characters, - and _."""
        if not USERNAME_RE.match(username):
            raise ValueError(
                "Username cannot contain special characters other than underscores and dashes."
            )
        return username

    @validator("password")
    def _validate_password(cls, password: str) -> str:
        """Checks if password is longer than 6 characters."""
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        return password


class UserInSignup(UserInLogin):
    """Model representing user at signup."""

    email: EmailStr
