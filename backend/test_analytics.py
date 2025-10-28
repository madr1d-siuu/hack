import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.services.analytics_service import get_transaction_stats

# Получаем статистику
stats = get_transaction_stats()

print("📊 АНАЛИТИКА ТРАНЗАКЦИЙ")
print("=" * 40)
print(f"📈 Всего транзакций: {stats['total_count']}")
print(f"✅ Одобрено: {stats['approved_count']}")
print(f"⚠️  Подозрительных: {stats['suspicious_count']}")
print(f"📥 В обработке: {stats['received_count']}")
print(f"📅 Сегодня: {stats['periods']['today']}")
print(f"📅 За неделю: {stats['periods']['week']}") 
print(f"📅 За месяц: {stats['periods']['month']}")
print("🔍 Статистика правил:")
for rule_id, rule_data in stats['rule_stats'].items():
    print(f"   Правило {rule_id}: {rule_data['triggered']}/{rule_data['total']} срабатываний")
print("=" * 40)