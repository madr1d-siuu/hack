import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.services.rule_history_service import save_rule_history

# Тест создания истории
history = save_rule_history(
    rule_id=1,
    changed_by="admin",
    change_type="update",
    old_values={"risk_score": 50, "is_active": True},
    new_values={"risk_score": 80, "is_active": False}
)

print("✅ История правила сохранена!")
print(f"📝 ID: {history.id}")
print(f"🔧 Тип изменения: {history.change_type}")
print(f"👤 Изменил: {history.changed_by}")
print(f"📅 Дата: {history.created_at}")