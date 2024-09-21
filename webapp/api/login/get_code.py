from fastapi import Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from webapp.api.login.router import auth_router
from webapp.crud.get_code import get_code_from_database
from webapp.db.postgres import get_session
# from webapp.schema.user.base import UserModel
from webapp.schema.login.user import UserIdTG


@auth_router.post(
    '/get_code',
    tags=['auth'],
)
async def get_code(
        body: UserIdTG,
        session: AsyncSession = Depends(get_session),
) -> ORJSONResponse:
    code = await get_code_from_database(session, body)

    return ORJSONResponse({'code': code}, status_code=status.HTTP_200_OK)
