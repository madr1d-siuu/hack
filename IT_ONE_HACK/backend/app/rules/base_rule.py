from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime


class RuleResult:
    """
    Структура результата оценки правила.
    passed     — True, если правило пройдено (не сработало).
    risk_score — значение риска (0.0–1.0).
    details    — любая дополнительная информация.
    timestamp  — время оценки.
    """
    def __init__(self, passed: bool, risk_score: float, details: Dict[str, Any]):
        self.passed = passed
        self.risk_score = risk_score
        self.details = details
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "risk_score": self.risk_score,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() + "Z"
        }


class BaseRule(ABC):
    def __init__(
        self,
        rule_id: int,
        name: str,
        enabled: bool = True,
        parameters: Dict[str, Any] = None,
        priority: int =5
    ):
        self.rule_id = rule_id
        self.name = name
        self.enabled = enabled
        self.parameters = parameters or {}
        self.priority = priority

    @abstractmethod
    def evaluate(self, transaction: Dict[str, Any]) -> RuleResult:
        """
        Оценивает транзакцию.
        Возвращает RuleResult.
        """
        ...

    def get_name(self) -> str:
        """Имя правила."""
        return self.name

    def is_enabled(self) -> bool:
        """Активно ли правило."""
        return self.enabled

    def get_priority(self) -> int: 
        return self.priority
    
    def is_critical(self) -> bool: 
        """Проверяет, является ли правило критическим (priority=1)"""
        return self.priority == 1

    def set_enabled(self, enabled: bool):
        """Включает/отключает правило."""
        self.enabled = enabled

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id={self.rule_id}, name='{self.name}', enabled={self.enabled})>"
        )
