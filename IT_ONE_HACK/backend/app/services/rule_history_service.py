import json
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import RuleHistory

def save_rule_history(rule_id: int, changed_by: str, change_type: str, old_values: dict = None, new_values: dict = None):
    """
    Сохраняет историю изменений правила
    """
    db = SessionLocal()
    try:
        history = RuleHistory(
            rule_id=rule_id,
            changed_by=changed_by,
            change_type=change_type,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        return history
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()