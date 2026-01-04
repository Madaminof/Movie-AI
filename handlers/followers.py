from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

async def get_stats(session: AsyncSession):
    query = select(func.count(User.id))
    result = await session.execute(query)
    return result.scalar()