from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.pagination import PageParams


async def paginate[T](
    session: AsyncSession, query: Select[tuple[T]], params: PageParams, *order_by: Any
) -> tuple[list[T], int]:
    """One page of `query` plus the total number of matching rows.

    Callers should end `order_by` with the primary key as a tie-breaker, so rows with
    equal timestamps keep a stable order and never repeat or vanish between pages.
    """
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    page = query.order_by(*order_by).offset(params.offset).limit(params.size)
    return list(await session.scalars(page)), total or 0
