from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from webapp.models.sirius.user import User
from webapp.schema.login.user import UserIdTG


async def get_code_from_database(session: AsyncSession, body: UserIdTG) -> str:
    result = await session.execute(select(User).where(User.username == body.username))
    user_data = result.scalar_one_or_none()
    return user_data.code if user_data else ''
