import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    return_none_on_failure: bool = False
):
    """
    Декоратор для повторных попыток выполнения асинхронных методов.
    
    Args:
        max_attempts: Максимальное количество попыток (по умолчанию 3)
        delay: Задержка между попытками в секундах (по умолчанию 1.0)
        return_none_on_failure: Если True, возвращает None вместо
            поднятия исключения
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        url = kwargs.get('url', 'неизвестному URL')
                        logger.warning(
                            f"Попытка {attempt + 1}/{max_attempts} "
                            f"неудачна для {func.__name__} "
                            f"к {url}: {str(e)}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        # Последняя попытка неудачна
                        logger.warning(
                            f"Все {max_attempts} попыток неудачны для "
                            f"{func.__name__}: {str(e)}"
                        )
            
            # Если все попытки неудачны
            if return_none_on_failure:
                return None
            else:
                # Поднимаем последнее исключение
                raise last_exception
        
        return wrapper
    return decorator
