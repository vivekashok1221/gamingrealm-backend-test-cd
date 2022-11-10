import re
from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, EmailStr, validator

from prisma.models import Post, PostComment
from prisma.partials import UserInLogin_
from src.backend.paginate_db import Page

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


class UserProfileResponse(BaseModel):
    """Data returned by the /user/{id} endpoint."""

    id: str
    username: str
    email: str
    created_at: datetime
    following_count: int
    follower_count: int
    posts_count: int
    posts: Page[Post]
    is_following: bool | None


class PostDetails(BaseModel):
    """Data returned for a specific post.

    The comments are paginated, and the first page of comments are included with the first response.
    """

    post: Post
    comments: Page[PostComment]


class PostCreateBody(BaseModel):
    """Describes the fields needed to create a new post."""

    title: str
    text_content: str
    media: list[AnyHttpUrl]
    tags: list[str]  # tag NAMES, not ids
