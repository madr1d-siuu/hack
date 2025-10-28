import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.workers.transaction_worker import process_transaction
from app.services.transaction_service import create_transaction

# Тест 1: Нормальная транзакция
normal_tx = create_transaction({
    "transaction_id": f"normal_{os.urandom(4).hex()}",
    "amount": 500.0,
    "currency": "USD",
    "merchant": "amazon",
    "user_id": "user_123"
})

result1 = process_transaction(normal_tx)
print(f"✅ Нормальная транзакция: {result1}")

# Тест 2: Подозрительная транзакция  
suspicious_tx = create_transaction({
    "transaction_id": f"suspicious_{os.urandom(4).hex()}",
    "amount": 15000.0,
    "currency": "USD",
    "merchant": "unknown_shop",
    "user_id": "user_456"
})

result2 = process_transaction(suspicious_tx)
print(f"✅ Подозрительная транзакция: {result2}")