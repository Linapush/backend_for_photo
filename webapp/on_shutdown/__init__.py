from webapp.db import kafka
from webapp.db import rabbitmq


async def stop_producer() -> None:
    await kafka.producer.stop()

# async def stop_rabbit() -> None:
#     await rabbitmq.channel.close()