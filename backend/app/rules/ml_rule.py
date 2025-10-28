import logging
from typing import Any, Dict

from .base_rule import BaseRule, RuleResult
from backend.app.services.ml_service import get_ml_model


logger = logging.getLogger(__name__)

class MLRule(BaseRule):
    def __init__(self, rule_id:int, name:str, enabled = True, parameters = None):
        super().__init__(rule_id, name, enabled, parameters)

    # Валидация параметров
        if "threshold" not in self.parameters:
            raise ValueError("MLRule requires 'threshold' in parameters")
        
        self.threshold = float(self.parameters["threshold"])
        
        if not (0.0 <= self.threshold <= 1.0):
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {self.threshold}")
        
        self.features_list = self.parameters.get("features", ["amount", "hour", "day_of_week"])
        self.ml_model = get_ml_model()
        
        logger.info(f"MLRule initialized with threshold={self.threshold}")

    def evaluate(self, transaction: Dict[str, Any]) -> RuleResult:
        """
        Оценивает транзакцию с помощью ML-модели.
        """
        try:
            # Извлекаем признаки
            features = self.ml_model.extract_features(transaction)
            
            # Получаем предсказание модели
            fraud_probability = self.ml_model.predict(features)
            
            # Сравниваем с порогом
            condition_met = fraud_probability >= self.threshold
            
            if condition_met:
                return RuleResult(
                    passed=False,
                    risk_score=fraud_probability,
                    details={
                        "reason": f"ML model detected fraud probability: {fraud_probability:.3f} >= {self.threshold}",
                        "fraud_probability": fraud_probability,
                        "threshold": self.threshold,
                        "features": features,
                        "condition_met": True
                    }
                )
            else:
                return RuleResult(
                    passed=True,
                    risk_score=fraud_probability,
                    details={
                        "reason": f"ML model fraud probability below threshold: {fraud_probability:.3f} < {self.threshold}",
                        "fraud_probability": fraud_probability,
                        "threshold": self.threshold,
                        "features": features,
                        "condition_met": False
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in MLRule evaluation: {e}")
            return RuleResult(
                passed=True,
                risk_score=0.0,
                details={
                    "reason": f"ML model error: {str(e)}",
                    "error": True
                }
            )

    def __repr__(self):
        return (
            f"<MLRule id={self.rule_id} name='{self.name}' "
            f"threshold={self.threshold}>"
        )