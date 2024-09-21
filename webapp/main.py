from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from webapp.api.file.router import file_router, filter_router
from webapp.api.login.router import auth_router
from webapp.metrics import metrics
from webapp.on_shutdown import stop_producer
from webapp.on_startup.kafka import create_producer
from webapp.on_startup.rabbit import start_rabbit
from webapp.on_startup.redis import start_redis


class Message(BaseModel):
    text: str


@auth_router.post("/start")
async def start_command(message: Message):
    return {"message": "Бот начал работу"}


# устанавливающаем CORS-middleware для приложения
def setup_middleware(app: FastAPI) -> None:
    # CORS Middleware should be the last.
    # See https://github.com/tiangolo/fastapi/issues/1663 .
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],  # разрешение запросов из всех доменов
        allow_credentials=True,  # разрешение на отправку куки
        allow_methods=['*'],  # разрешение всех HTTP-методов
        allow_headers=['*'],  # разрешение все заголовков
    )


def setup_routers(app: FastAPI) -> None:
    app.add_route('/metrics', metrics)

    app.include_router(auth_router)
    app.include_router(file_router)
    app.include_router(filter_router)


# асинхнронный контекстный менеджер lifespan
# позволяет выполнять определенные действия при запуске и остановке приложения
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await start_redis()
    await start_rabbit()
    await create_producer()
    print('START APP')
    yield
    await stop_producer()
    print('END APP')


# объект приложения FastAPI с документацией по Swagger и заданным контекстным менеджером
# устанавливает CORS-middleware
def create_app() -> FastAPI:
    app = FastAPI(docs_url='/swagger', lifespan=lifespan)

    setup_middleware(app)
    setup_routers(app)

    return app
