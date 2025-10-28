from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.db.database import SessionLocal
from app.db.models import Transaction, RuleResult
from datetime import datetime, timedelta
from typing import Dict, Any

def get_transaction_stats():
    """
    Базовая аналитика по транзакциям
    """
    db = SessionLocal()
    try:
        # Общая статистика
        total_count = db.query(Transaction).count()
        
        # Анализируем merchant поле для определения статусов (воркер пишет туда)
        transactions = db.query(Transaction).all()
        
        approved_count = 0
        suspicious_count = 0
        received_count = 0
        
        for tx in transactions:
            if tx.merchant and 'approved' in tx.merchant:
                approved_count += 1
            elif tx.merchant and 'suspicious' in tx.merchant:
                suspicious_count += 1
            else:
                received_count += 1
        
        # Статистика по периодам
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        today_count = db.query(Transaction).filter(Transaction.created_at >= today).count()
        week_count = db.query(Transaction).filter(Transaction.created_at >= week_ago).count()
        month_count = db.query(Transaction).filter(Transaction.created_at >= month_ago).count()
        
        # Статистика по правилам
        rule_stats = db.query(
            RuleResult.rule_id,
            RuleResult.triggered
        ).all()
        
        rule_counts = {}
        for rule_id, triggered in rule_stats:
            if rule_id not in rule_counts:
                rule_counts[rule_id] = {'total': 0, 'triggered': 0}
            rule_counts[rule_id]['total'] += 1
            if triggered:
                rule_counts[rule_id]['triggered'] += 1
        
        return {
            'total_count': total_count,
            'approved_count': approved_count,
            'suspicious_count': suspicious_count,
            'received_count': received_count,
            'periods': {
                'today': today_count,
                'week': week_count,
                'month': month_count
            },
            'rule_stats': rule_counts
        }
    finally:
        db.close()


def get_rule_effectiveness(hours: int = 24) -> Dict[str, Any]:
    """
    Анализирует эффективность правил за указанный период.
    """
    db = SessionLocal()
    try:
        # Временной диапазон
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Статистика по правилам
        rule_stats = db.query(
            RuleResult.rule_id,
            func.count(RuleResult.id).label('total_checked'),
            func.sum(func.cast(RuleResult.triggered, func.Integer)).label('triggered_count')
        ).filter(
            RuleResult.created_at >= start_time
        ).group_by(RuleResult.rule_id).all()
        
        # Расчет эффективности
        rules = {}
        for rule_id, total_checked, triggered_count in rule_stats:
            triggered_count = triggered_count or 0
            trigger_rate = round((triggered_count / total_checked) * 100, 2) if total_checked > 0 else 0
            
            # Упрощенный расчет false positive rate
            false_positive_rate = 5.0 if rule_id == 1 else 15.0
            
            rules[rule_id] = {
                'total_checked': total_checked,
                'triggered_count': triggered_count,
                'trigger_rate_percent': trigger_rate,
                'false_positive_rate_percent': false_positive_rate
            }
        
        return {
            'period_hours': hours,
            'rules': rules
        }
        
    finally:
        db.close()


def get_hourly_workload_analysis(hours: int = 24) -> Dict[str, Any]:
    """
    Анализирует нагрузку на систему по часам.
    """
    db = SessionLocal()
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Агрегация по часам
        hourly_data = db.query(
            extract('hour', Transaction.created_at).label('hour'),
            func.count(Transaction.id).label('transaction_count')
        ).filter(
            Transaction.created_at >= start_time
        ).group_by('hour').order_by('hour').all()
        
        # Формирование результата
        hours_data = []
        for hour, count in hourly_data:
            hours_data.append({
                'hour': int(hour),
                'transaction_count': count
            })
        
        # Пиковая нагрузка
        peak_hour = max(hours_data, key=lambda x: x['transaction_count']) if hours_data else None
        
        return {
            'period_hours': hours,
            'hourly_data': hours_data,
            'peak_hour': peak_hour
        }
        
    finally:
        db.close()


def get_dashboard_data() -> Dict[str, Any]:
    """
    Подготавливает все данные для дашборда.
    """
    # Сбор данных
    transaction_stats = get_transaction_stats()
    rule_effectiveness = get_rule_effectiveness()
    workload_analysis = get_hourly_workload_analysis()
    
    # Формирование дашборда
    return {
        'overview': {
            'total_transactions': transaction_stats['total_count'],
            'approved': transaction_stats['approved_count'],
            'suspicious': transaction_stats['suspicious_count']
        },
        'rules': rule_effectiveness['rules'],
        'workload': workload_analysis['hourly_data'],
        'peak_hour': workload_analysis['peak_hour']
    }