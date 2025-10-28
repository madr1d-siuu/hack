from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import AdminAuditLog

def log_admin_action(user: str, action: str, details: str = None, ip_address: str = None, user_agent: str = None):
    """
    Логирует действия администратора
    """
    db = SessionLocal()
    try:
        log = AdminAuditLog(
            user=user,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()