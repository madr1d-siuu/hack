from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Numeric, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Transaction(Base):
    """Модель для хранения финансовых транзакций"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    correlation_id = Column(String, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    merchant = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="received", index=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    rule_results = relationship("RuleResult", back_populates="transaction")

class Rule(Base):
    """Модель анти-фрод правил"""
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False, default="threshold")
    condition = Column(Text, nullable=False)
    risk_score = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=5, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RuleResult(Base):
    """Модель результатов применения правил"""
    __tablename__ = "rule_results"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id"), nullable=False)
    triggered = Column(Boolean, default=False)
    risk_score = Column(Integer)
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    transaction = relationship("Transaction", back_populates="rule_results")
    rule = relationship("Rule")

# Индексы для производительности
Index('idx_transaction_correlation_id', Transaction.correlation_id)
Index('idx_transaction_status', Transaction.status)
Index('idx_transaction_created_at', Transaction.created_at)
Index('idx_rule_result_transaction_id', RuleResult.transaction_id)