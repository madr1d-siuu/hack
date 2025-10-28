from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Transaction
from datetime import datetime
import uuid
from typing import List, Dict, Any

def create_transaction(transaction_data: dict):
    """Создание новой транзакции"""
    db = SessionLocal()
    try:
        # Генерируем ID если не предоставлен
        transaction_id = transaction_data.get("transaction_id") or str(uuid.uuid4())
        
        transaction = Transaction(
            transaction_id=transaction_id,
            amount=transaction_data["amount"],
            currency=transaction_data["currency"],
            merchant=transaction_data["merchant"],
            user_id=transaction_data["user_id"],
            timestamp=transaction_data.get("timestamp", datetime.now()),
            description=transaction_data.get("description"),
            status="received"
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_transaction(transaction_id: str):
    """Получение транзакции по ID"""
    db = SessionLocal()
    try:
        return db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    finally:
        db.close()

def update_transaction_status(transaction_id: str, status: str):
    """Обновление статуса транзакции"""
    db = SessionLocal()
    try:
        transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        if transaction:
            transaction.status = status
            db.commit()
            db.refresh(transaction)
        return transaction
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_all_transactions(skip: int = 0, limit: int = 100, status: str = None):
    """Получение списка транзакций с пагинацией и фильтрацией"""
    db = SessionLocal()
    try:
        query = db.query(Transaction)
        if status:
            query = query.filter(Transaction.status == status)
        return query.offset(skip).limit(limit).all()
    finally:
        db.close()

def get_transaction_stats():
    """Получение статистики по транзакциям"""
    db = SessionLocal()
    try:
        total = db.query(Transaction).count()
        approved = db.query(Transaction).filter(Transaction.status == "approved").count()
        suspicious = db.query(Transaction).filter(Transaction.status == "suspicious").count()
        blocked = db.query(Transaction).filter(Transaction.status == "blocked").count()
        
        return {
            "total_transactions": total,
            "approved_count": approved,
            "suspicious_count": suspicious,
            "blocked_count": blocked
        }
    finally:
        db.close()