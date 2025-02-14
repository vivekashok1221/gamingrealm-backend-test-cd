from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Form, Header, HTTPException, Query, UploadFile
from loguru import logger

from prisma.errors import PrismaError
from prisma.models import Post, PostComment, PostMedia, PostRating
from src.backend.dependencies import is_authorized
from src.backend.models import CreatePostResponse, MessageResponse, PostDetails
from src.backend.paginate_db import Page, paginate
from src.backend.storage import _upload_to_storage

router = APIRouter(prefix="/post", tags=["post"])
authz_router = APIRouter(dependencies=[Depends(is_authorized)])


@router.get("/")
async def get_posts(
    take: int = Header(default=10),
    cursor: str | None = Header(default=None),
    uid: str | None = Query(default=None),
    tag: str | None = Query(default=None),
) -> Page[Post]:
    """Paginate and get posts based on specified filters (user, tag etc).

    Expects pagination headers:
        take: The number of items to be retrieved in one page
        cursor: The ID of the last fetched item
    """
    filters = {}
    if uid:
        filters["author_id"] = uid
    if tag:
        filters["tags"] = {"some": {"tag_name": tag}}
    filters["deleted"] = False

    return await paginate(
        Post,
        take,
        cursor,
        where=filters,
        include={"tags": True, "author": True},
        order={"created_at": "desc"},
    )


@authz_router.post("/create", response_model=CreatePostResponse)
async def create_post(
    title: Annotated[str, Form()],
    text_content: Annotated[str | None, Form()] = None,
    images: list[UploadFile] | None = None,
    user_id: UUID | None = Header(default=None),
) -> dict[str, Any]:
    """Create a new post."""
    try:
        inserted_post = await Post.prisma().create(
            data={
                "author": {"connect": {"id": str(user_id)}},
                "title": title,
                "text_content": text_content,
            },
        )
    except PrismaError as e:
        logger.warning(f"Could not create post: {e}")
        raise HTTPException(422, "Could not create the post due to an internal error")

    response = inserted_post.dict(exclude={"media": True})
    if images is not None:
        file_path = f"{user_id}/{inserted_post.id}"
        urls = await _upload_to_storage(images, file_path)

        await PostMedia.prisma().create_many(
            data=[{"post_id": inserted_post.id, "object_url": url} for url in urls]
        )
        response["urls"] = urls
    return response


@router.get("/search")
async def search_posts(
    q: str = Query(),
) -> Page[Post]:
    """Gets posts based on specified query.

    Matching is done using Full Text Search
    """
    words = q.split()
    search_phrase = " & ".join(words)
    query = (
        'SELECT * from "Post" WHERE to_tsvector("title") @@ to_tsquery($1)'
        ' ORDER BY "created_at" LIMIT 20'
    )
    posts = await Post.prisma().query_raw(query, search_phrase)
    return Page(data=posts, count=len(posts), cursor_id=None)


@router.get("/{id}")
async def get_post(id: str) -> PostDetails:
    """Get full details of a specific post."""
    post = await Post.prisma().find_first(
        where={"id": id, "deleted": False}, include={"tags": True, "media": True, "author": True}
    )
    if not post:
        raise HTTPException(404, "Post not found")
    comments = await paginate(
        PostComment,
        page_size=20,
        where={"post_id": id},
        include={"author": True},
        order={"created_at": "desc"},
    )
    avg_rating_query = await PostRating.prisma().group_by(
        by=["post_id"], avg={"value": True}, having={"post_id": id}
    )
    avg_rating = round(avg_rating_query[0]["_avg"]["value"])  # type: ignore
    return PostDetails(post=post, comments=comments, avg_rating=avg_rating)


@authz_router.delete("/{id}")
async def delete_post(
    id: str,
    user_id: UUID | None = Header(default=None),
) -> MessageResponse:
    """Delete a post."""
    try:
        # this endpoint only soft-deletes
        # update_many is used as update forces you to query with only fields that can
        # uniquely identify a row
        # and we need to filter by author_id as well
        deleted_post = await Post.prisma().update_many(
            data={"deleted": True}, where={"id": id, "author_id": str(user_id)}
        )
    except PrismaError as e:
        logger.warning(f"Could not delete post: {e}")
        raise HTTPException(400, "Could not delete the post due to an internal error")
    if not deleted_post:
        raise HTTPException(404, "Post not found")
    return MessageResponse(message="Post deleted.")


@authz_router.post("/{post_id}/comments")
async def create_comment(
    post_id: str,
    comment_text: str = Body(),
    user_id: UUID | None = Header(default=None),
) -> PostComment:
    """Create a comment on the specified post."""
    try:
        comment = await PostComment.prisma().create(
            data={
                "author_id": str(user_id),
                "post_id": post_id,
                "content": comment_text,
                "author": {"connect": {"id": str(user_id)}},
                "post": {"connect": {"id": post_id}},
            }
        )
    except PrismaError as e:
        logger.warning(f"Could not create comment: {e}")
        raise HTTPException(400, "Could not create the comment due to an internal error")
    return comment


@router.get("/{post_id}/comments")
async def get_comments(
    post_id: str, take: int = Header(default=10), cursor: str | None = Header(default=None)
) -> Page[PostComment]:
    """Paginate and get the comments of a post.

    Expects pagination headers:
        take: The number of items to be retrieved in one page
        cursor: The ID of the last fetched item
    """
    return await paginate(
        PostComment,
        take,
        cursor,
        where={"post_id": post_id},
        include={"author": True},
        order={"created_at": "desc"},
    )


@authz_router.delete("/{post_id}/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    user_id: UUID | None = Header(default=None),
) -> MessageResponse:
    """Endpoint to delete a comment."""
    try:
        deleted_comment = await PostComment.prisma().delete_many(
            where={"id": comment_id, "author_id": str(user_id)}
        )
    except PrismaError as e:
        logger.warning(f"Could not delete comment: {e}")
        raise HTTPException(400, "Could not delete the comment due to an internal error")
    if not deleted_comment:
        raise HTTPException(404, "The current user has not created a comment with the provided ID.")
    return MessageResponse(message="Comment deleted.")


router.include_router(authz_router)
