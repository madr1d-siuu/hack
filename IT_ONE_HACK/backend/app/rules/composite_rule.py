import logging
from typing import Dict, Any, List
from .base_rule import BaseRule, RuleResult
logger = logging.getLogger(__name__)

class CompositeRule(BaseRule):
    def __init__(self, rule_id: int, name:str, enabled = True, parameters = None,rules_registry: Dict[int, BaseRule] = None,priority:int=5):
        super().__init__(rule_id, name, enabled, parameters,priority)
         
         # Валидация параметров
        if "operator" not in self.parameters or "rules" not in self.parameters:
            raise ValueError("CompositeRule requires 'operator' and 'rules' in parameters")
        
        self.operator = self.parameters["operator"].upper()
        if self.operator not in ("AND", "OR"):
            raise ValueError(f"Unsupported operator '{self.operator}'. Use 'AND' or 'OR'")
        
        self.nested_rule_ids = self.parameters["rules"]
        if not isinstance(self.nested_rule_ids, list) or len(self.nested_rule_ids) == 0:
            raise ValueError("CompositeRule requires non-empty list of rule IDs")
        
        self.rules_registry = rules_registry or {}
        self.custom_risk_score = self.parameters.get("risk_score")

    def evaluate(self, transaction: Dict[str, Any]) -> RuleResult:
        """
        Рекурсивно оценивает все вложенные правила и комбинирует результаты
        в зависимости от оператора AND/OR.
        """
        nested_results = []
        nested_risk_scores = []
        
        # Проверяем все вложенные правила
        for rule_id in self.nested_rule_ids:
            nested_rule = self.rules_registry.get(rule_id)
            
            if not nested_rule:
                logger.warning(f"Nested rule {rule_id} not found in registry")
                continue
            
            if not nested_rule.is_enabled():
                logger.debug(f"Nested rule {rule_id} is disabled, skipping")
                continue
            
            try:
                result = nested_rule.evaluate(transaction)
                nested_results.append({
                    "rule_id": rule_id,
                    "rule_name": nested_rule.get_name(),
                    "passed": result.passed,
                    "risk_score": result.risk_score,
                    "details": result.details
                })
                nested_risk_scores.append(result.risk_score)
            except Exception as e:
                logger.error(f"Error evaluating nested rule {rule_id}: {e}")
                nested_results.append({
                    "rule_id": rule_id,
                    "error": str(e)
                })
        
        if not nested_results:
            logger.warning(f"No valid nested rules evaluated in CompositeRule {self.rule_id}")
            return RuleResult(
                passed=True,
                risk_score=0.0,
                details={
                    "reason": "No valid nested rules",
                    "operator": self.operator,
                    "nested_rule_ids": self.nested_rule_ids
                }
            )
        
        # Применяем логический оператор
        if self.operator == "AND":
            # Все правила должны НЕ пройти (passed=False), чтобы композитное правило сработало
            all_failed = all(not r["passed"] for r in nested_results if "passed" in r)
            condition_met = all_failed
        else:  # OR
            # Хотя бы одно правило должно НЕ пройти (passed=False)
            any_failed = any(not r["passed"] for r in nested_results if "passed" in r)
            condition_met = any_failed
        
        # Вычисляем агрегированный риск-скор
        if self.custom_risk_score is not None:
            # Используем заданный риск-скор
            aggregated_risk = float(self.custom_risk_score)
        elif nested_risk_scores:
            # Среднее значение риск-скоров вложенных правил
            aggregated_risk = sum(nested_risk_scores) / len(nested_risk_scores)
        else:
            aggregated_risk = 0.0
        
        if condition_met:
            return RuleResult(
                passed=False,
                risk_score=aggregated_risk,
                details={
                    "reason": f"Composite rule triggered ({self.operator})",
                    "operator": self.operator,
                    "nested_results": nested_results,
                    "aggregated_risk_score": aggregated_risk,
                    "condition_met": True
                }
            )
        else:
            return RuleResult(
                passed=True,
                risk_score=0.0,
                details={
                    "reason": f"Composite rule not triggered ({self.operator})",
                    "operator": self.operator,
                    "nested_results": nested_results,
                    "condition_met": False
                }
            )

    def __repr__(self):
        rule_ids = ", ".join(str(rid) for rid in self.nested_rule_ids)
        return (
            f"<CompositeRule id={self.rule_id} name='{self.name}' "
            f"operator={self.operator} rules=[{rule_ids}]>"
        )