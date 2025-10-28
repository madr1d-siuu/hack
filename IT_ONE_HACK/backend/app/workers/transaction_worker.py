import asyncio
import time
from typing import Dict, Any
from app.db.redis import redis_client
from app.core.logging import get_logger
from app.services.transaction_service import update_transaction_status
from app.services.rule_result_service import save_rule_result

logger = get_logger(__name__)

class SimpleTransactionWorker:
    def __init__(self):
        self.is_running = False
        self.processed_count = 0
    
    async def process_queue(self, delay: float = 1.0):
        self.is_running = True
        logger.info("Transaction worker started")
        
        while self.is_running:
            try:
                transaction_data = await redis_client.pop_transaction()
                
                if transaction_data:
                    success = await self.process_transaction(transaction_data)
                    if success:
                        self.processed_count += 1
                
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(delay)
    
    async def process_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        transaction_id = transaction_data.get('id', 'unknown')
        
        try:
            logger.info(f"Processing transaction: {transaction_id}")
            
            # Импортируем rule_engine внутри функции чтобы избежать circular import
            from app.rules.rule_engine import rule_engine
            evaluation_result = rule_engine.evaluate_transaction(transaction_data)
            
            # Сохраняем результаты каждого правила
            for rule_result in evaluation_result.get('details', []):
                if 'rule_id' in rule_result:
                    save_rule_result(
                        transaction_id=transaction_id,
                        rule_id=rule_result['rule_id'],
                        result=rule_result
                    )
            
            # Определяем финальный статус
            final_status = self.determine_status(evaluation_result)
            
            # Обновляем статус транзакции
            update_transaction_status(transaction_id, final_status)
            
            logger.info(f"Transaction {transaction_id} processed. Status: {final_status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process transaction {transaction_id}: {e}")
            update_transaction_status(transaction_id, "failed")
            return False
    
    def determine_status(self, evaluation_result: Dict[str, Any]) -> str:
        if not evaluation_result.get('is_suspicious', False):
            return "approved"
        
        risk_score = evaluation_result.get('risk_score', 0)
        
        if risk_score >= 80:
            return "blocked"
        elif risk_score >= 50:
            return "suspicious"
        else:
            return "approved"
    
    async def stop(self):
        self.is_running = False
        logger.info("Transaction worker stopped")

# Глобальный экземпляр воркера
worker = SimpleTransactionWorker()

async def start_worker(delay: float = 1.0):
    await worker.process_queue(delay)

async def stop_worker():
    await worker.stop()

def get_worker_status():
    return {
        "is_running": worker.is_running,
        "processed_count": worker.processed_count
    }