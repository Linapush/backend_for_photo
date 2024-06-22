from fastapi import Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from webapp.db.postgres import get_session
from starlette import status
from webapp.api.login.router import auth_router
# from webapp.schema.user.base import UserModel
from webapp.schema.login.user import UserIdTG
from webapp.crud.get_code import get_code_from_database
from webapp.models.sirius.user import User


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
