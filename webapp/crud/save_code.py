from webapp.models.sirius.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from webapp.schema.login.user import UserLogin


async def save_code_to_database(session: AsyncSession, body: UserLogin) -> None:
    user = User(username=body.username, code=body.code)
    async with session.begin():
        session.add(user)
        await session.commit()
