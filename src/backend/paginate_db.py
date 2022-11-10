"""Functions to paginate queries to the database."""
from typing import Generic, Type, TypeVar

from loguru import logger
from pydantic.generics import GenericModel

from prisma.models import Post, PostComment, User

_ModelT = TypeVar("_ModelT", User, Post, PostComment)


class Page(GenericModel, Generic[_ModelT]):
    """Represents a page of database objects.

    The cursor_id is Null if the query returned no responses.
    """

    data: list[_ModelT]
    count: int
    cursor_id: str | None


async def paginate(
    model: Type[_ModelT], page_size: int, cursor_id: str | None = None, **kwargs
) -> Page[_ModelT]:
    """Make a paginated database query."""
    if cursor_id:
        logger.info(f"Making page query: {model}, page size={page_size}")
        data = await model.prisma().find_many(take=page_size, cursor={"id": cursor_id}, **kwargs)
    else:
        data = await model.prisma().find_many(take=page_size, **kwargs)
    try:
        cursor_id = data[-1].id
    except IndexError:
        cursor_id = None
    return Page(data=data, count=len(data), cursor_id=cursor_id)  # type: ignore
