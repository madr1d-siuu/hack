"""
ПРОСТОЙ СКРИПТ ДЛЯ ТЕСТОВЫХ ДАННЫХ MVP
"""
from app.db.database import SessionLocal
from app.db.models import Rule, Transaction
from datetime import datetime

def init_test_data():
    """Добавляем тестовые правила и транзакции"""
    db = SessionLocal()
    
    try:
        # 1. Добавляем правила
        rules = [
            Rule(name="high_amount", description="Сумма > 10000", condition="amount > 10000", risk_score=80),
            Rule(name="suspicious_merchant", description="Подозрительные магазины", condition="merchant = 'unknown'", risk_score=60),
        ]
        
        for rule in rules:
            db.add(rule)
        
        # 2. Добавляем транзакции
        transactions = [
            Transaction(transaction_id="tx1", amount=500.0, currency="USD", merchant="amazon", user_id="user1", timestamp=datetime.now()),
            Transaction(transaction_id="tx2", amount=15000.0, currency="USD", merchant="unknown", user_id="user2", timestamp=datetime.now()),
        ]
        
        for tx in transactions:
            db.add(tx)
        
        db.commit()
        print("✅ Тестовые данные добавлены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_test_data()