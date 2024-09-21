import logging
from contextvars import ContextVar

import yaml

with open('conf/logging.conf.yml', 'r') as f:  # открываетя файл конфигурации в режиме чтения
    LOGGING_CONFIG = yaml.full_load(f)


class ConsoleFormatter(logging.Formatter):  # кастомный форматтер

    def format(self,
               record: logging.LogRecord) -> str:  # переопределяем метод `format`, чтобы добавить корреляционный идентификатор к сообщениям логирования, если он доступен
        try:  # отслеживание запросов в многопоточной среде
            correlation_id = correlation_id_ctx.get()  # пытаемся получить значение корреляционого идентификатора из контекстной пременной
            return '[%s] %s' % (correlation_id, super().format(record))
        except LookupError:
            return super().format(record)


correlation_id_ctx = ContextVar(
    'correlation_id_ctx')  # создаем объект `correlation_id_ctx` типа `ContextVar`, который используется для хранения корреляционного идентификатора
logger = logging.getLogger(
    'photo_tinder_bot')  # создается объект логгера с именем `'photo_tinder_bot'` с помощью `logging.getLogger
