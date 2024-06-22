from webapp.cache.rabbit.key_builder import get_user_files_queue_key
from webapp.db.rabbitmq import get_channel, get_exchange_users

# declare_queue - объявить очередь

async def declare_queue(user_id: int) -> None:
    channel = get_channel() # получаем канал (`channel`) для взаимодействия с RabbitMQ

    queue_key = get_user_files_queue_key(user_id)

    exchange_users = get_exchange_users() # получаем обменник?
    queue = await channel.declare_queue(queue_key, auto_delete=False, durable=True) # объявляем очередь с использованием полученного ключа

    await queue.bind(exchange_users, queue_key) #привязываем созданную очередь к обменнику

# declare_queue объявляет очередь для пользователя
# Сначала получаем канал (`channel`) для взаимодействия с RabbitMQ.
# Затем вызывается функция get_user_products_queue_key из key_builder.py, чтобы получить ключ очереди для конкретного пользователя.
# Далее получается обменник (`exchange_users`) и объявляется очередь с использованием полученного ключа.
# Наконец, происходит привязка созданной очереди к обменнику.