from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BIND_IP: str
    BIND_PORT: int
    DB_URL: str

    DB_HOST: str = 'web_db_dev'
    DB_PORT: int = 5433
    DB_USERNAME: str = 'postgres'
    DB_PASSWORD: str = 'postgres'
    DB_NAME: str = 'main_db'

    # JWT, Kafka
    JWT_SECRET_SALT: str  # секретный ключ, используемый для подписи JSON Web Tokens (JWT), обеспечивая безопасность веб-приложений и API
    KAFKA_BOOTSTRAP_SERVERS: List[str]  # распределенная платформа для обработки данных в реальном времени.
    KAFKA_TOPIC: str

    # Redis - система управления базами данных, используемая как кэш, база данных или очередь сообщений
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_SIRIUS_CACHE_PREFIX: str = 'sirius'

    # Rabbit, Minio
    RABBIT_SIRIUS_USER_PREFIX: str = 'user'  # идентификации различных экземпляров RabbitMQ
    TEMP_FILES_DIR: str = '/temp'  # директория, в которой временные файлы будут сохраняться или использоваться при работе программы
    MINIO_ACCESS_KEY: str  # сервер для облачного хранения данных, совместимый с Amazon S3. Настройки MinIO могут включать параметры подключения к серверу, доступ и другие параметры
    MINIO_SECRET_KEY: str
    MINIO_HOST: str
    MINIO_PORT: str


settings = Settings()
