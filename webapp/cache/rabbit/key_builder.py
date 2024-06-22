from conf.config import settings


# получаем ключ, создаем префикс 
def get_user_files_queue_key(user_id: int) -> str:
    return f'{settings.RABBIT_SIRIUS_USER_PREFIX}:{user_id}'

# функция принимает user_id и возвращает строку, 
# состоящую из префикса из настроек (`RABBIT_SIRIUS_USER_PREFIX`) и user_id

# затем в -> queue 