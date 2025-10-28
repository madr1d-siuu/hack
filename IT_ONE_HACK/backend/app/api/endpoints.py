from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response
from typing import Dict, Any, List
import uuid
from datetime import datetime
import csv
from io import StringIO

from app.core.models import TransactionCreate, TransactionResponse, ErrorResponse, RuleCreate, RuleResponse
from app.core.logging import get_logger
from app.db.database import SessionLocal, get_db
from app.db.models import Transaction, Rule, RuleResult
from app.services.transaction_service import create_transaction, get_transaction_stats, get_all_transactions
from app.services.rule_service import load_rules_from_db
from app.services.analytics_service import get_dashboard_data
from sqlalchemy.orm import Session

logger = get_logger(__name__)

router = APIRouter()

# Transaction endpoints
@router.post(
    "/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_transaction_endpoint(transaction: TransactionCreate, request: Request, db: Session = Depends(get_db)):
    """
    Создание новой транзакции
    """
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    
    try:
        logger.info(f"Creating transaction - Correlation ID: {correlation_id}")
        
        # Генерируем ID для транзакции
        transaction_id = str(uuid.uuid4())
        
        # Создаем объект ответа
        transaction_response = TransactionResponse(
            id=transaction_id,
            correlation_id=correlation_id,
            status="received",
            **transaction.dict()
        )
        
        # Сохраняем в БД
        transaction_data = transaction.dict()
        transaction_data["transaction_id"] = transaction_id
        db_transaction = create_transaction(transaction_data)
        
        logger.info(f"Transaction created successfully - ID: {transaction_id}")
        
        return transaction_response
        
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="InternalServerError",
                message="Failed to create transaction",
                correlation_id=correlation_id
            ).dict()
        )

@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse
)
async def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """
    Получение транзакции по ID
    """
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="NotFound",
                message=f"Transaction {transaction_id} not found",
                correlation_id="unknown"
            ).dict()
        )
    
    return TransactionResponse(
        id=transaction.transaction_id,
        correlation_id=transaction.correlation_id or "unknown",
        status=transaction.status,
        amount=float(transaction.amount),
        currency=transaction.currency,
        merchant=transaction.merchant,
        user_id=transaction.user_id,
        timestamp=transaction.timestamp,
        description=transaction.description,
        created_at=transaction.created_at
    )

# Admin endpoints
@router.get("/admin/transactions")
async def get_transactions_admin(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Получить транзакции для админки
    """
    transactions = get_all_transactions(skip=skip, limit=limit, status=status)
    
    return {
        "transactions": [
            {
                "id": tx.transaction_id,
                "amount": float(tx.amount),
                "currency": tx.currency,
                "merchant": tx.merchant,
                "user_id": tx.user_id,
                "status": tx.status,
                "created_at": tx.created_at
            }
            for tx in transactions
        ],
        "total": len(transactions)
    }

@router.get("/admin/transactions/{transaction_id}")
async def get_transaction_admin(transaction_id: str, db: Session = Depends(get_db)):
    """
    Получить детали транзакции для админки
    """
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    rule_results = db.query(RuleResult).filter(RuleResult.transaction_id == transaction.id).all()
    
    return {
        "transaction": {
            "id": transaction.transaction_id,
            "correlation_id": transaction.correlation_id,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "merchant": transaction.merchant,
            "user_id": transaction.user_id,
            "status": transaction.status,
            "timestamp": transaction.timestamp,
            "description": transaction.description,
            "created_at": transaction.created_at
        },
        "rule_results": [
            {
                "rule_id": rr.rule_id,
                "triggered": rr.triggered,
                "risk_score": rr.risk_score,
                "details": rr.details
            }
            for rr in rule_results
        ]
    }

@router.get("/admin/rules")
async def get_rules_admin(db: Session = Depends(get_db)):
    """
    Получить все правила для админки
    """
    rules = db.query(Rule).all()
    
    return {
        "rules": [
            {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "type": rule.type,
                "condition": rule.condition,
                "risk_score": rule.risk_score,
                "is_active": rule.is_active,
                "priority": rule.priority,
                "created_at": rule.created_at
            }
            for rule in rules
        ]
    }

@router.post("/admin/rules")
async def create_rule_admin(rule_data: RuleCreate, db: Session = Depends(get_db)):
    """
    Создать новое правило через админку
    """
    try:
        rule = Rule(
            name=rule_data.name,
            description=rule_data.description,
            type=rule_data.type,
            condition=rule_data.condition,
            risk_score=rule_data.risk_score,
            is_active=rule_data.is_active,
            priority=rule_data.priority
        )
        
        db.add(rule)
        db.commit()
        db.refresh(rule)
        
        # Перезагружаем правила в rule_engine
        from app.rules.rule_engine import rule_engine
        from app.services.rule_service import load_rules_from_db
        rules_dict = load_rules_from_db(db)
        rule_engine.load_rules(list(rules_dict.values()))
        
        return {"message": "Rule created successfully", "rule_id": rule.id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/admin/analytics")
async def get_analytics_admin(db: Session = Depends(get_db)):
    """
    Получить данные для аналитики
    """
    stats = get_transaction_stats()
    
    # Простая аналитика по часам (для демо)
    transactions = db.query(Transaction).all()
    hourly_data = {hour: 0 for hour in range(24)}
    
    for tx in transactions:
        hour = tx.created_at.hour
        hourly_data[hour] = hourly_data.get(hour, 0) + 1
    
    return {
        "stats": stats,
        "hourly_data": [
            {"hour": hour, "count": count}
            for hour, count in hourly_data.items()
        ]
    }

@router.get("/export/transactions")
async def export_transactions(db: Session = Depends(get_db)):
    """
    Экспорт транзакций в CSV
    """
    transactions = db.query(Transaction).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow(['ID', 'Amount', 'Currency', 'Merchant', 'User ID', 'Status', 'Created At'])
    
    # Данные
    for tx in transactions:
        writer.writerow([
            tx.transaction_id,
            float(tx.amount),
            tx.currency,
            tx.merchant,
            tx.user_id,
            tx.status,
            tx.created_at.isoformat()
        ])
    
    output.seek(0)
    
    return Response(
        content=output.getvalue(),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=transactions.csv'}
    )