from fastapi import Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from webapp.db.postgres import get_session
from starlette import status
from webapp.api.login.router import auth_router
from webapp.schema.login.user import UserLogin, UserLoginResponse
# from webapp.schema.user.base import UserModel
from webapp.crud.save_code import save_code_to_database
 

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
