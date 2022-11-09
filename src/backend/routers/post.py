from uuid import UUID

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from loguru import logger

from prisma.errors import PrismaError
from prisma.models import Post, PostComment
from src.backend.auth.sessions import AbstractSessionStorage
from src.backend.dependencies import get_sessions, is_authorized
from src.backend.models import PostCreateBody, PostDetails
from src.backend.paginate_db import Page, paginate

router = APIRouter(prefix="/post")


@router.get("/")
async def get_posts(
    take: int = Query(default=10),
    uid: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
) -> Page[Post]:
    """Paginate and get posts based on specified filters (user, tag etc)."""
    filters = {}
    if uid:
        filters["author_id"] = uid
    if tag:
        filters["tag"] = {"tag_name": tag}
    return await paginate(Post, take, cursor, where=filters, order={"created_at": "desc"})


@router.get("/{id}", response_model=PostDetails)
async def get_post(id: str) -> PostDetails:
    """Get full details of a specific post."""
    post = await Post.prisma().find_first(
        where={"id": id}, include={"tags": True, "media": True, "author": True}
    )
    if not post:
        raise HTTPException(404, "Post not found")
    comments = await paginate(
        PostComment, page_size=20, where={"post_id": id}, order={"created_at": "desc"}
    )
    return PostDetails(post=post, comments=comments)


@router.post("/create", response_model=Post)
async def create_post(
    post: PostCreateBody = Body(embed=True),
    user_id: UUID | None = Header(default=None),
    session_id: UUID | None = Header(default=None, alias="session-id"),
    sessions: AbstractSessionStorage = Depends(get_sessions),
) -> Post:
    """Create a new post."""
    await is_authorized(user_id, session_id, sessions)
    try:
        inserted_post = await Post.prisma().create(
            {
                "author_id": str(user_id),
                "title": post.title,
                "text_content": post.text_content,
                "media": {"create": [{"object_url": url} for url in post.media]},
                "tags": {"connect": [{"tag_name": tname} for tname in post.tags]},
            }
        )
    except PrismaError as e:
        logger.warning(f"Could not create post: {e}")
        raise HTTPException(422, "Could not create the post due to an internal error")
    return inserted_post


@router.delete("/{id}")
async def delete_post(
    id: str,
    user_id: UUID | None = Header(default=None),
    session_id: UUID | None = Header(default=None, alias="session-id"),
    sessions: AbstractSessionStorage = Depends(get_sessions),
) -> JSONResponse:
    """Delete a post."""
    await is_authorized(user_id, session_id, sessions)
    try:
        deleted_post = await Post.prisma().update(data={"deleted": True}, where={"id": id})
    except PrismaError as e:
        logger.warning(f"Could not delete post: {e}")
        raise HTTPException(400, "Could not delete the post due to an internal error")
    if not deleted_post:
        return JSONResponse({"message": "Post did not exist"}, status_code=400)
    return JSONResponse({"message": "Post deleted"}, status_code=200)
