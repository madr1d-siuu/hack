import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from app.core.logging import get_logger, set_correlation_id

logger = get_logger(__name__)

class CorrelationMiddleware(BaseHTTPMiddleware):
    """Простой middleware для отслеживания запросов через correlation_id"""
    async def dispatch(self, request: Request, call_next):
        # Устанавливаем correlation_id
        correlation_id = request.headers.get('X-Correlation-ID')
        cid = set_correlation_id(correlation_id)
        
        start_time = time.time()
        
        try:
            # Обрабатываем запрос
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            # Логируем успешный запрос
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "processing_time": round(processing_time, 4),
                    "correlation_id": cid
                }
            )
            
            # Добавляем correlation_id в заголовки ответа
            response.headers["X-Correlation-ID"] = cid
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Логируем ошибку
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path, 
                    "processing_time": round(processing_time, 4),
                    "correlation_id": cid,
                    "error": str(e)
                },
                exc_info=True
            )
            raise