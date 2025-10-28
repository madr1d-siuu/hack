import logging
import random
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MLModelSimulator:
    """
    Эмулятор ML-модели для обнаружения мошенничества.
    """
    
    def __init__(self):
        logger.info("MLModelSimulator initialized (demo mode)")
    
    def extract_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлекает признаки из транзакции для модели.
        
        Базовые признаки:
        - amount: сумма транзакции
        - hour: час дня (0-23)
        - day_of_week: день недели (0-6)
        - is_weekend: выходной день или нет
        """
        features = {}
        
        # Сумма транзакции
        features['amount'] = float(transaction.get('amount', 0))
        
        # Время транзакции
        timestamp = transaction.get('timestamp')
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = timestamp
                features['hour'] = dt.hour
                features['day_of_week'] = dt.weekday()
                features['is_weekend'] = 1 if dt.weekday() >= 5 else 0
            except Exception as e:
                logger.warning(f"Failed to parse timestamp: {e}")
                features['hour'] = 12
                features['day_of_week'] = 0
                features['is_weekend'] = 0
        else:
            # Значения по умолчанию
            features['hour'] = 12
            features['day_of_week'] = 0
            features['is_weekend'] = 0
        
        # Дополнительные поля
        features['merchant'] = transaction.get('merchant', 'unknown')
        features['currency'] = transaction.get('currency', 'USD')
        
        return features
    
    def predict(self, features: Dict[str, Any]) -> float:
        """
        Генерирует предсказание модели (эмуляция).
        
        Для демонстрации используем простую эвристику:
        - Большая сумма + ночное время = выше риск
        - В остальных случаях - случайное значение
        """
        amount = features.get('amount', 0)
        hour = features.get('hour', 12)
        
        # Эвристика для демонстрации
        base_risk = random.uniform(0.1, 0.4)
        
        # Увеличиваем риск для больших сумм
        if amount > 100000:
            base_risk += 0.3
        elif amount > 50000:
            base_risk += 0.15
        
        # Увеличиваем риск для ночного времени
        if hour >= 22 or hour <= 5:
            base_risk += 0.2
        
        # Ограничиваем значение в диапазоне [0, 1]
        risk_score = min(1.0, max(0.0, base_risk))
        
        logger.debug(f"ML prediction: features={features}, risk_score={risk_score:.3f}")
        return risk_score


# Глобальный экземпляр модели
_ml_model = None


def get_ml_model() -> MLModelSimulator:
    """Возвращает singleton экземпляр ML-модели"""
    global _ml_model
    if _ml_model is None:
        _ml_model = MLModelSimulator()
    return _ml_model
