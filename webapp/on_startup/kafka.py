async def create_producer() -> None:
    pass
    # kafka.producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    #
    # await kafka.producer.start()
    #
    # kafka.partitions = list(await kafka.producer.partitions_for(settings.KAFKA_TOPIC))
