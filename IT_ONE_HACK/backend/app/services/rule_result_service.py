"""
ОТДЕЛЬНЫЙ СЕРВИС ДЛЯ СОХРАНЕНИЯ РЕЗУЛЬТАТОВ ПРАВИЛ
(без зависимостей от redis и других модулей)
"""
import json
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import RuleResult

def save_rule_result(transaction_id: int, rule_id: int, result: dict):
    """
    Сохраняет результат проверки правила для транзакции
    """
    db = SessionLocal()
    try:
        rule_result = RuleResult(
            transaction_id=transaction_id,
            rule_id=rule_id,
            triggered=result["passed"],
            risk_score=result["risk_score"],
            details=json.dumps(result["details"])
        )
        db.add(rule_result)
        db.commit()
        db.refresh(rule_result)
        return rule_result
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()