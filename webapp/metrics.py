import os

import prometheus_client
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, CollectorRegistry, generate_latest
from prometheus_client.multiprocess import MultiProcessCollector
from starlette.requests import Request
from starlette.responses import Response

#

DEFAULT_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.075,
    0.1,
    0.125,
    0.15,
    0.175,
    0.2,
    0.25,
    0.3,
    0.5,
    0.75,
    1.0,
    2.5,
    5.0,
    7.5,
    float('+inf'),
)

# TODO in middleware
# prometheus_client.Counter(
#     'sirius_deps_latency_seconds',
#     '',
#     ['endpoint'],
# )

# задержка при взаимодействии с внешними зависимостями
# histogram_quantile(0.99, sum(rate(sirius_deps_latency_seconds_bucket[1m])) by (le, endpoint))
# среднее время обработки за 1 мин
DEPS_LATENCY = prometheus_client.Histogram(
    'sirius_deps_latency_seconds',
    '',
    ['endpoint'],
    buckets=DEFAULT_BUCKETS,
)

# задержка операций взаимодействия с базами данных и Redis
INTEGRATION_LATENCY_DB_REDIS = prometheus_client.Histogram(
    'integration_latency_db_redis_seconds',
    'Time taken for integration operations with DB, Redis, etc.',
    ['operation'],
    buckets=DEFAULT_BUCKETS,
)

# задержка операций взаимодействия с бекендом и Telegram
INTEGRATION_LATENCY_BACKEND_TELEGRAM = prometheus_client.Histogram(
    'integration_latency_backend_telegram_seconds',
    'Time taken for integration operations with backend and Telegram',
    ['operation'],
    buckets=DEFAULT_BUCKETS,
)

import time


# ...

def metrics(request: Request) -> Response:
    if 'prometheus_multiproc_dir' in os.environ:
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
    else:
        registry = REGISTRY

    return Response(generate_latest(registry), headers={'Content-Type': CONTENT_TYPE_LATEST})


def some_db_operation():
    start_time = time.time()

    # операция запроса в БД или других хранилищ данных

    end_time = time.time()
    execution_time = end_time - start_time

    INTEGRATION_LATENCY_DB_REDIS.labels(operation='db_query').observe(execution_time)


def some_backend_operation():
    start_time = time.time()

    # операция взаимодействия с бекендом

    end_time = time.time()
    execution_time = end_time - start_time

    INTEGRATION_LATENCY_BACKEND_TELEGRAM.labels(operation='backend_call').observe(execution_time)


def some_external_service_operation(endpoint: str):
    start_time = time.time()

    # операция взаимодействия с внешним сервисом

    end_time = time.time()
    execution_time = end_time - start_time

    DEPS_LATENCY.labels(endpoint=endpoint).observe(execution_time)
