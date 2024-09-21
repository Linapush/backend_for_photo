from fastapi import Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from webapp.api.login.router import auth_router
# from webapp.schema.user.base import UserModel
from webapp.crud.save_code import save_code_to_database
from webapp.db.postgres import get_session
from webapp.schema.login.user import UserLogin


@auth_router.post(
    '/save_code',
    tags=['auth'],
)
async def save_code(
        body: UserLogin,
        session: AsyncSession = Depends(get_session),
) -> ORJSONResponse:
    # await save_code_to_database(session, user_id, username, code)
    await save_code_to_database(session, body)

    return ORJSONResponse({'message': 'Код сохранен успешно'}, status_code=status.HTTP_200_OK)
