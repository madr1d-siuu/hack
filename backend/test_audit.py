import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.services.audit_service import log_admin_action

# Тест логирования действий
log1 = log_admin_action(
    user="admin",
    action="login",
    details="Успешный вход в систему",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

log2 = log_admin_action(
    user="admin", 
    action="create_rule",
    details="Создано правило 'high_amount'",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

log3 = log_admin_action(
    user="admin",
    action="update_rule", 
    details="Обновлено правило ID 1: risk_score 50 -> 80",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

print("✅ Аудит действий администратора:")
print(f"📝 Вход: {log1.action} - {log1.details}")
print(f"📝 Создание: {log2.action} - {log2.details}") 
print(f"📝 Изменение: {log3.action} - {log3.details}")
print(f"🌐 IP: {log1.ip_address}")
print(f"🔍 User-Agent: {log1.user_agent[:50]}...")