from fastapi import APIRouter

from prisma.models import Tag

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=list[Tag])
async def get_tags() -> list[Tag]:
    """Get all existing tags."""
    return await Tag.prisma().find_many()
