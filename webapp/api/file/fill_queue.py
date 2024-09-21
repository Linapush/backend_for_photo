import msgpack
from aio_pika import Message
from fastapi import Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from webapp.api.file.router import file_router
from webapp.db.postgres import get_session
from webapp.db.rabbitmq import get_exchange_users
from webapp.models.sirius.file import File
from webapp.schema.file.file import FillQueue


@file_router.post('/fill_queue')
async def fill_queue(
        body: FillQueue = Depends(),
        session: AsyncSession = Depends(get_session),
        # access_token: JwtTokenT = Depends(jwt_auth.validate_token),
) -> ORJSONResponse:
    exchange_users = get_exchange_users()

    files = await session.stream_scalars(select(File).order_by(func.random()))
    async for file in files:
        await exchange_users.publish(
            Message(
                msgpack.packb({'file_id': file.id}),
                content_type='text/plain',
                headers={'foo': 'bar'}
            ),
            ''
        )

    return ORJSONResponse(
        {
            'status': 'success',
        }
    )
