import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import sys
from contextvars import ContextVar

# Context variable для хранения correlation_id
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

class JSONFormatter(logging.Formatter):
    """Кастомный форматтер для логирования в JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Форматирует log record в JSON строку
        """
        # Базовая структура лога
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Добавляем correlation_id если есть
        current_correlation_id = correlation_id.get()
        if current_correlation_id:
            log_entry["correlation_id"] = current_correlation_id
        
        # Добавляем exception информацию если есть
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Добавляем дополнительные поля из record.args
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            log_entry.update(record.extra_data)
        
        return json.dumps(log_entry, ensure_ascii=False)

def get_correlation_id() -> Optional[str]:
    """Получить текущий correlation_id"""
    return correlation_id.get()

def set_correlation_id(cid: Optional[str] = None) -> str:
    """
    Установить correlation_id
    
    Args:
        cid: correlation_id. Если None - генерируется новый
        
    Returns:
        str: Установленный correlation_id
    """
    if cid is None:
        cid = str(uuid.uuid4())
    
    correlation_id.set(cid)
    return cid

def clear_correlation_id() -> None:
    """Очистить correlation_id"""
    correlation_id.set(None)

class CorrelationFilter(logging.Filter):
    """Фильтр для добавления correlation_id в log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        current_cid = correlation_id.get()
        if current_cid:
            record.correlation_id = current_cid  # type: ignore
        return True

def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None
) -> None:
    """
    Настройка логирования
    
    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Использовать JSON формат
        log_file: Путь к файлу для записи логов (опционально)
    """
    # Получаем root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Очищаем существующие handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Создаем formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(CorrelationFilter())
    logger.addHandler(console_handler)
    
    # File handler (если указан файл)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.addFilter(CorrelationFilter())
        logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Получить настроенный логгер
    
    Args:
        name: Имя логгера (обычно __name__)
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    return logging.getLogger(name)

# Декоратор для автоматической трассировки
def traced_function(logger_name: str = None):
    """
    Декоратор для автоматического логирования вызовов функций
    
    Args:
        logger_name: Имя логгера (если None, используется имя модуля)
    """
    def decorator(func):
        nonlocal logger_name
        if logger_name is None:
            logger_name = func.__module__
        
        logger = get_logger(logger_name)
        
        def wrapper(*args, **kwargs):
            cid = set_correlation_id()
            logger.info(
                "Function started",
                extra={"extra_data": {
                    "function": func.__name__,
                    "correlation_id": cid,
                    "action": "function_start"
                }}
            )
            
            try:
                result = func(*args, **kwargs)
                logger.info(
                    "Function completed",
                    extra={"extra_data": {
                        "function": func.__name__,
                        "correlation_id": cid,
                        "action": "function_complete"
                    }}
                )
                return result
            except Exception as e:
                logger.error(
                    "Function failed",
                    extra={"extra_data": {
                        "function": func.__name__,
                        "correlation_id": cid,
                        "action": "function_error",
                        "error": str(e)
                    }},
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator

# Инициализация логирования при импорте
setup_logging(level="INFO", json_format=True)