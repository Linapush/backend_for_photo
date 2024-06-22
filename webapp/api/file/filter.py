from typing import List, Optional

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from webapp.api.file.router import filter_router
from webapp.crud.filter import get_filtered_data
from webapp.db.postgres import get_session
from webapp.utils.auth.jwt import JwtTokenT, jwt_auth


@filter_router.get('/', response_model=List[int], tags=['filter'])
async def get_filtered_data_endpoint(
    year: Optional[int] = None,
    month: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
    access_token: JwtTokenT = Depends(jwt_auth.get_current_user),
):
    try:
        filtered = await get_filtered_data(session=session, user_id=access_token['user_id'], year=year, month=month)

        if filtered is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Ничего не найдено.')

        return filtered
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
