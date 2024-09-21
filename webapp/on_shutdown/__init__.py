from webapp.db import kafka


async def stop_producer() -> None:
    await kafka.producer.stop()

# async def stop_rabbit() -> None:
#     await rabbitmq.channel.close()
