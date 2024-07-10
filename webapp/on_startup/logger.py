import logging.config

from conf.config import settings
from webapp.logger import LOGGING_CONFIG, logger


def setup_logger() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)

    if settings.LOG_LEVEL == 'INFO':
        logger.setLevel(logging.DEBUG)
