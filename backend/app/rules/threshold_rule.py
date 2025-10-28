from typing import Dict, Any
from .base_rule import BaseRule, RuleResult
import logging

logger = logging.getLogger(__name__)


class ThresholdRule(BaseRule):
    OPERATORS = {
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }

    def __init__(self, rule_id: int, name: str, enabled: bool = True, parameters: Dict[str, Any] = None,priority: int=5):
        super().__init__(rule_id, name, enabled, parameters,priority)
        
        # Валидация параметров
        required = ["field", "operator", "value"]
        for key in required:
            if key not in self.parameters:
                raise ValueError(f"ThresholdRule requires '{key}' in parameters")
        
        if self.parameters["operator"] not in self.OPERATORS:
            raise ValueError(
                f"Unsupported operator: {self.parameters['operator']}. "
                f"Supported: {list(self.OPERATORS.keys())}"
            )

    def evaluate(self, transaction: Dict[str, Any]) -> RuleResult:
        """
        Проверяет транзакцию на соответствие пороговому условию.
        
        Args:
            transaction: словарь с данными транзакции
            
        Returns:
            RuleResult с полями:
            - passed: False если правило сработало (условие выполнено)
            - risk_score: значение риска (из parameters или 0.8 по умолчанию)
            - details: информация о проверке
        """
        field = self.parameters["field"]
        operator = self.parameters["operator"]
        threshold_value = self.parameters["value"]
        risk_score = self.parameters.get("risk_score", 0.8)
        
        # Получаем значение поля из транзакции
        if field not in transaction:
            logger.warning(f"Field '{field}' not found in transaction")
            return RuleResult(
                passed=True,
                risk_score=0.0,
                details={
                    "reason": f"Field '{field}' not found in transaction",
                    "field": field,
                    "operator": operator,
                    "threshold": threshold_value
                }
            )
        
        transaction_value = transaction[field]
        
        # Применяем оператор
        condition_met = self.OPERATORS[operator](transaction_value, threshold_value)
        
        if condition_met:
            # Условие выполнено — правило сработало (транзакция подозрительная)
            return RuleResult(
                passed=False,
                risk_score=risk_score,
                details={
                    "reason": f"{field} {operator} {threshold_value} (actual: {transaction_value})",
                    "field": field,
                    "operator": operator,
                    "threshold": threshold_value,
                    "actual_value": transaction_value,
                    "condition_met": True
                }
            )
        else:
            # Условие не выполнено — правило не сработало (транзакция нормальная)
            return RuleResult(
                passed=True,
                risk_score=0.0,
                details={
                    "reason": f"{field} {operator} {threshold_value} not met (actual: {transaction_value})",
                    "field": field,
                    "operator": operator,
                    "threshold": threshold_value,
                    "actual_value": transaction_value,
                    "condition_met": False
                }
            )

    def __repr__(self):
        return (
            f"<ThresholdRule(id={self.rule_id}, name='{self.name}', "
            f"field={self.parameters.get('field')}, "
            f"operator={self.parameters.get('operator')}, "
            f"value={self.parameters.get('value')})>"
        )

