import json
import logging
from sqlalchemy.orm import Session
from app.db.models import Rule
from app.rules.threshold_rule import ThresholdRule
from app.rules.pattern_rule import PatternRule
from app.rules.composite_rule import CompositeRule
from app.rules.ml_rule import MLRule

logger = logging.getLogger(__name__)

_active_rules_cache = {}

def load_rules_from_db(db_session: Session):
    """
    Загружает все активные правила из БД и создаёт их экземпляры.
    Возвращает словарь {rule_id: rule_instance}.
    """
    rules_dict = {}
    
    try:
        '''Загружаем и сортируем по priority (ASC: 1, 2, 3... — от высокого к низкому)'''
        db_rules = (db_session.query(Rule).filter_by(is_active=True).order_by(Rule.priority.asc()).all())
        logger.info(f"Found {len(db_rules)} active rules in database")
        
        for db_rule in db_rules:
            try:
                # Парсим JSON параметры из поля condition
                parameters = json.loads(db_rule.condition)
                
                # Определяем тип правила
                rule_type = db_rule.type.lower() if hasattr(db_rule, 'type') else 'threshold'
                
                # Создаём экземпляр правила в зависимости от типа
                if rule_type == "threshold":
                    instance = ThresholdRule(
                        rule_id=db_rule.id,
                        name=db_rule.name,
                        enabled=db_rule.is_active,
                        parameters=parameters,
                        priority= db_rule.priority
                    )
                elif rule_type == "pattern":
                    instance = PatternRule(
                        rule_id=db_rule.id,
                        name=db_rule.name,
                        enabled=db_rule.is_active,
                        parameters=parameters,
                        priority = db_rule.priority
                    )
                elif rule_type == "composite":
                    instance=CompositeRule(
                        rule_id=db_rule.id,
                        name=db_rule.name,
                        enabled=db_rule.is_active,
                        parameters=parameters,
                        rules_registry=rules_dict,
                        priority = db_rule.priority
                    )
                elif rule_type == "ml":
                    instance = MLRule(
                        rule_id=db_rule.id,
                        name=db_rule.name,
                        enabled=db_rule.is_active,
                        parameters=parameters,
                        priority = db_rule.priority
                    )
                else:
                    logger.warning(f"Unknown rule type '{rule_type}' for rule_id={db_rule.id}")
                    continue
                
                rules_dict[db_rule.id] = instance
                logger.info(f"Loaded rule: {instance}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse parameters for rule_id={db_rule.id}: {e}")
                continue
            except Exception as e:
                logger.error(f"Failed to create rule instance for rule_id={db_rule.id}: {e}")
                continue
        
        logger.info(f"Successfully loaded {len(rules_dict)} rules")
        return rules_dict
        
    except Exception as e:
        logger.error(f"Failed to load rules from database: {e}")
        return {}

def reload_rules(db_session: Session):
    """
    Перезагружает правила из БД и обновляет кэш в памяти
    """
    global _active_rules_cache
    
    try:
        # Загружаем правила из БД
        new_rules = load_rules_from_db(db_session)
        
        # Обновляем кэш
        _active_rules_cache = new_rules
        
        # Логируем факт перезагрузки
        logger.info(f"Rules reloaded successfully. Active rules in cache: {len(_active_rules_cache)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to reload rules: {e}")
        return False

def get_active_rules():
    return _active_rules_cache

def clear_rules_cache():
    global _active_rules_cache
    _active_rules_cache = {}
    logger.info("Rules cache cleared")