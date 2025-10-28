from app.db.database import engine, Base
from app.db.models import Transaction, Rule, RuleResult

def create_tables():
    print("🔄 Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы успешно!")
    print("📊 Созданы таблицы: transactions, rules, rule_results, rule_history, admin_audit_logs")

if __name__ == "__main__":
    create_tables()