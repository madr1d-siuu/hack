import os
import json
import logging
from typing import Optional, Any, Dict
import redis.asyncio as redis
from app.core.logging import get_logger, traced_function

logger = get_logger(__name__)

class RedisClient:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.queue_key = "transaction_queue"

    @traced_function(__name__)
    async def init_redis(self):
        """Инициализация подключения к Redis"""
        try:
            redis_host = os.getenv("REDIS_HOST", "redis")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(
                "Failed to connect to Redis",
                extra={"extra_data": {"error": str(e)}},
                exc_info=True
            )
            raise

    async def close_redis(self):
        """Закрытие подключения к Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    @traced_function(__name__)
    async def push_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """Добавление транзакции в очередь"""
        try:
            if not self.redis_client:
                await self.init_redis()

            transaction_json = json.dumps(transaction_data, ensure_ascii=False)
            result = await self.redis_client.lpush(self.queue_key, transaction_json)
            
            logger.info(
                "Transaction pushed to queue",
                extra={"extra_data": {
                    "queue_length": result,
                    "transaction_id": transaction_data.get("id")
                }}
            )
            return True
            
        except Exception as e:
            logger.error(
                "Error pushing transaction to Redis",
                extra={"extra_data": {
                    "error": str(e),
                    "transaction_id": transaction_data.get("id")
                }},
                exc_info=True
            )
            return False

    @traced_function(__name__)
    async def pop_transaction(self) -> Optional[Dict[str, Any]]:
        """Извлечение транзакции из очереди"""
        try:
            if not self.redis_client:
                await self.init_redis()

            transaction_json = await self.redis_client.rpop(self.queue_key)
            
            if transaction_json:
                transaction_data = json.loads(transaction_json)
                logger.info(
                    "Transaction popped from queue",
                    extra={"extra_data": {
                        "transaction_id": transaction_data.get("id")
                    }}
                )
                return transaction_data
            else:
                logger.debug("Queue is empty")
                return None
                
        except Exception as e:
            logger.error(
                "Error popping transaction from Redis",
                extra={"extra_data": {"error": str(e)}},
                exc_info=True
            )
            return None

    @traced_function(__name__)
    async def get_queue_length(self) -> int:
        """Получение длины очереди"""
        try:
            if not self.redis_client:
                await self.init_redis()

            length = await self.redis_client.llen(self.queue_key)
            logger.debug(
                "Queue length retrieved",
                extra={"extra_data": {"queue_length": length}}
            )
            return length
            
        except Exception as e:
            logger.error(
                "Error getting queue length from Redis",
                extra={"extra_data": {"error": str(e)}},
                exc_info=True
            )
            return 0

redis_client = RedisClient()