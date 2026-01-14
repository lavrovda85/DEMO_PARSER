import asyncio
from functools import wraps


def async_retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Декоратор для повторных попыток выполнения асинхронных методов.
    
    Args:
        max_attempts: Максимальное количество попыток (по умолчанию 3)
        delay: Задержка между попытками в секундах (по умолчанию 1.0)
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
                        # Получаем экземпляр класса для логирования
                        self = args[0] if args else None
                        if hasattr(self, 'write_debug'):
                            self.write_debug(f"Попытка {attempt + 1}/{max_attempts} неудачна для {func.__name__}: {str(e)}")
                        await asyncio.sleep(delay)
                    else:
                        # Последняя попытка неудачна
                        if hasattr(self, 'write_warning'):
                            self.write_warning(f"Все {max_attempts} попыток неудачны для {func.__name__}: {str(e)}")
            
            # Если все попытки неудачны, поднимаем последнее исключение
            raise last_exception
        
        return wrapper
    return decorator