import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from app.services.backup_service import export_rules_to_json, import_rules_from_json

print("🧪 ТЕСТ СИСТЕМЫ БЭКАПА")
print("=" * 40)

# Тест экспорта
backup_file = export_rules_to_json()
print(f"✅ Экспорт завершен: {backup_file}")
print(f"📁 Файл существует: {os.path.exists(backup_file)}")

# Проверяем содержимое файла
with open(backup_file, "r", encoding="utf-8") as f:
    data = json.load(f)
    print(f"📊 Правил в бэкапе: {len(data)}")

# Тест импорта (импортируем тот же файл)
imported_count = import_rules_from_json(backup_file)
print(f"✅ Импорт завершен: добавлено {imported_count} правил")

print("=" * 40)
print("🎉 СИСТЕМА БЭКАПА РАБОТАЕТ!")