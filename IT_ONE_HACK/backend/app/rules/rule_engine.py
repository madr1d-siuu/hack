import logging
from typing import List, Dict, Any
from .base_rule import BaseRule

logger = logging.getLogger(__name__)

class RuleEngine:
    """
    Контейнер для управления правилами
    """
    def __init__(self):
        self.rules: List[BaseRule] = []
        logger.info("RuleEngine initialized")

    def load_rules(self, rules: List[BaseRule]):
        """Загружает правила и сортирует их по приоритету"""
        self.rules = sorted(rules, key=lambda r: r.get_priority())
        logger.info(f"Loaded {len(rules)} rules, sorted by priority")

    def add_rule(self, rule: BaseRule):
        """Добавляет новое правило"""
        self.rules.append(rule)
        logger.info(f"Added rule: {rule}")

    def remove_rule(self, rule_id: int):
        """Удаляет правило по ID"""
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        after = len(self.rules)
        logger.info(f"Removed rule_id={rule_id}. Count: {before}→{after}")

    def get_rule(self, rule_id: int) -> BaseRule:
        """Возвращает правило по ID или None"""
        return next((r for r in self.rules if r.rule_id == rule_id), None)

    def get_active_rules(self) -> List[BaseRule]:
        """Список активных правил"""
        return [r for r in self.rules if r.is_enabled()]

    def evaluate_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Оценивает транзакцию по всем активным правилам"""
        results = []
        total_score = 0.0
        triggered = []
        active = self.get_active_rules()

        logger.info(f"Evaluating transaction with {len(active)} rules")

        for rule in active:
            try:
                res = rule.evaluate(transaction)
                results.append({
                    "rule_id": rule.rule_id,
                    "rule_name": rule.get_name(),
                    "result": res.to_dict()
                })
                total_score += res.risk_score
                if not res.passed:
                    triggered.append(rule.get_name())
                    
                    # Проверяем критическое правило
                    if rule.is_critical():
                        logger.warning(f"CRITICAL RULE TRIGGERED: {rule.get_name()}. Stopping evaluation.")
                        break
            except Exception as e:
                logger.error(f"Error in rule {rule}: {e}")
                results.append({
                    "rule_id": rule.rule_id,
                    "rule_name": rule.get_name(),
                    "error": str(e)
                })

        avg_score = total_score / len(active) if active else 0.0
        return {
            "is_suspicious": len(triggered) > 0,
            "risk_score": avg_score,
            "triggered_rules": triggered,
            "checked_rules": len(active),
            "details": results
        }

    def reload_rules(self, new_rules: List[BaseRule]):
        """Hot-reload: заменяет правила на новые"""
        self.load_rules(new_rules)
        logger.info("Rules hot-reloaded")

    def summary(self) -> Dict[str, Any]:
        """Общая информация по правилам"""
        total = len(self.rules)
        active = len(self.get_active_rules())
        return {
            "total": total,
            "active": active,
            "inactive": total - active
        }

# Создаем экземпляр в конце файла
rule_engine = RuleEngine()