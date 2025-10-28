import logging
from typing import Dict, Any
from datetime import timedelta
import redis

from .base_rule import BaseRule, RuleResult

logger = logging.getLogger(__name__)

# Инициализация Redis-клиента 
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)


class PatternRule(BaseRule):
    def __init__(
        self,
        rule_id: int,
        name: str,
        enabled: bool = True,
        parameters: Dict[str, Any] = None,
        priority: int = 5
    ):
        super().__init__(rule_id, name, enabled, parameters,priority)
        if "max_transactions" not in self.parameters or "time_window_minutes" not in self.parameters:
            raise ValueError("PatternRule requires 'max_transactions' and 'time_window_minutes'")
        self.max_tx = int(self.parameters["max_transactions"])
        self.window = int(self.parameters["time_window_minutes"])
        self.field = self.parameters.get("field", "from_account")

    def evaluate(self, transaction: Dict[str, Any]) -> RuleResult:
        from_acc = transaction.get("from_account")
        if not from_acc:
            return RuleResult(
                passed=True,
                risk_score=0.0,
                details={"reason": "no from_account field"}
            )
        key = f"account:{from_acc}:count"
        # Увеличиваем счётчик и устанавливаем TTL, если новый ключ
        count = redis_client.incr(key)
        # Если первый раз, устанавливаем TTL
        if count == 1:
            redis_client.expire(key, self.window * 60)
        # Проверяем условие
        if count > self.max_tx:
            # сработало правило
            return RuleResult(
                passed=False,
                risk_score=0.5,
                details={
                    "reason": f"{count} transactions in last {self.window} minutes",
                    "from_account": from_acc,
                    "count": count,
                    "max_transactions": self.max_tx,
                    "time_window_minutes": self.window
                }
            )
        # не сработало
        return RuleResult(
            passed=True,
            risk_score=0.0,
            details={
                "reason": f"{count} transactions in last {self.window} minutes",
                "from_account": from_acc,
                "count": count,
                "max_transactions": self.max_tx,
                "time_window_minutes": self.window
            }
        )

    def __repr__(self):
        return (
            f"<PatternRule(id={self.rule_id}, name='{self.name}', "
            f"max_tx={self.max_tx}, window={self.window}m)>"
        )
