from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal

class TransactionCreate(BaseModel):
    """Модель для создания транзакции (входящие данные)"""
    
    amount: float = Field(..., gt=0, description="Сумма транзакции должна быть больше 0")
    currency: str = Field(default="USD", description="Валюта транзакции", max_length=3)
    merchant: str = Field(..., description="Магазин/сервис")
    user_id: str = Field(..., description="ID пользователя")
    timestamp: datetime = Field(..., description="Временная метка транзакции")
    description: Optional[str] = Field(None, description="Описание транзакции")
    
    @validator('timestamp')
    def validate_timestamp_not_in_future(cls, v):
        """Проверяет, что timestamp не из будущего"""
        if v > datetime.now(timezone.utc):
            raise ValueError('Timestamp cannot be in the future')
        return v
    
    @validator('currency')
    def validate_currency_length(cls, v):
        """Проверяет длину кода валюты"""
        if v and len(v) != 3:
            raise ValueError('Currency code must be 3 characters long')
        return v.upper() if v else v
    
    @validator('merchant', 'user_id')
    def validate_field_not_empty(cls, v):
        """Проверяет, что поле не пустое"""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

class TransactionResponse(BaseModel):
    """Модель ответа для транзакции"""
    
    id: str = Field(..., description="Уникальный идентификатор транзакции")
    status: Literal["received", "processing", "approved", "suspicious", "blocked"] = Field(
        default="received",
        description="Статус обработки транзакции"
    )
    correlation_id: str = Field(..., description="ID для трассировки запроса")
    amount: float = Field(..., description="Сумма транзакции")
    currency: str = Field(..., description="Валюта транзакции")
    merchant: str = Field(..., description="Магазин/сервис")
    user_id: str = Field(..., description="ID пользователя")
    timestamp: datetime = Field(..., description="Временная метка транзакции")
    description: Optional[str] = Field(None, description="Описание транзакции")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

class ErrorResponse(BaseModel):
    """Модель для ошибок API"""
    
    error: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Сообщение об ошибке")
    correlation_id: str = Field(..., description="ID для трассировки")
    details: Optional[Dict[str, Any]] = Field(None, description="Дополнительные детали ошибки")

class RuleCreate(BaseModel):
    """Модель для создания правила"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None)
    type: str = Field(..., description="Тип правила: threshold, pattern, composite, ml")
    condition: str = Field(..., description="Условие правила в JSON")
    risk_score: int = Field(..., ge=1, le=100)
    is_active: bool = Field(True)
    priority: int = Field(default=5, ge=1, le=10)

class RuleResponse(BaseModel):
    """Модель ответа для правила"""
    id: int
    name: str
    description: Optional[str]
    type: str
    condition: str
    risk_score: int
    is_active: bool
    priority: int
    created_at: datetime