import requests
import asyncio
import time
import json
import sys
import os

# Конфигурация
BASE_URL = "http://localhost:8000"
TEST_TRANSACTIONS = [
    {
        "amount": 150.50,
        "currency": "USD",
        "merchant": "Amazon",
        "user_id": "user_123",
        "timestamp": "2024-01-15T14:30:00Z",
        "description": "Normal online purchase"
    },
    {
        "amount": 50000.00,
        "currency": "USD",
        "merchant": "Unknown Merchant",
        "user_id": "user_456", 
        "timestamp": "2024-01-15T14:35:00Z",
        "description": "Large suspicious transfer"
    },
    {
        "amount": 25.00,
        "currency": "EUR",
        "merchant": "Starbucks",
        "user_id": "user_789",
        "timestamp": "2024-01-15T14:40:00Z",
        "description": "Coffee shop"
    }
]

class SystemTester:
    def __init__(self):
        self.created_transactions = []
        self.test_results = {}
    
    def print_step(self, message):
        print(f"\n🔹 {message}")
    
    def print_success(self, message):
        print(f"   ✅ {message}")
    
    def print_error(self, message):
        print(f"   ❌ {message}")
    
    def print_warning(self, message):
        print(f"   ⚠️  {message}")

    def test_health(self):
        """Тест здоровья системы"""
        self.print_step("1. Проверка здоровья системы")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                self.print_success(f"Health check: {response.json()}")
                return True
            else:
                self.print_error(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Health check error: {e}")
            return False

    def test_database_connection(self):
        """Тест подключения к БД"""
        self.print_step("2. Проверка подключения к БД")
        try:
            # Проверяем через API
            response = requests.get(f"{BASE_URL}/api/admin/transactions?limit=1", timeout=5)
            if response.status_code == 200:
                self.print_success("Database connection: OK")
                return True
            else:
                self.print_error(f"Database check failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Database check error: {e}")
            return False

    def test_redis_connection(self):
        """Тест подключения к Redis"""
        self.print_step("3. Проверка подключения к Redis")
        try:
            # Создаем тестовую транзакцию чтобы проверить очередь
            test_tx = {
                "amount": 1.00,
                "currency": "USD",
                "merchant": "Test",
                "user_id": "test_user",
                "timestamp": "2024-01-15T14:45:00Z"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/transactions",
                json=test_tx,
                headers={"X-Correlation-ID": f"test-redis-{int(time.time())}"},
                timeout=5
            )
            
            if response.status_code == 201:
                self.print_success("Redis queue: OK (transaction accepted)")
                return True
            else:
                self.print_error(f"Redis test failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Redis test error: {e}")
            return False

    def create_test_transactions(self):
        """Создание тестовых транзакций"""
        self.print_step("4. Создание тестовых транзакций")
        success_count = 0
        
        for i, tx_data in enumerate(TEST_TRANSACTIONS):
            try:
                correlation_id = f"test-{i}-{int(time.time())}"
                response = requests.post(
                    f"{BASE_URL}/api/transactions",
                    json=tx_data,
                    headers={"X-Correlation-ID": correlation_id},
                    timeout=5
                )
                
                if response.status_code == 201:
                    tx_id = response.json()["id"]
                    self.created_transactions.append(tx_id)
                    self.print_success(f"Transaction {i+1}: {tx_id} (${tx_data['amount']} {tx_data['currency']})")
                    success_count += 1
                else:
                    self.print_error(f"Transaction {i+1} failed: {response.status_code}")
                    
            except Exception as e:
                self.print_error(f"Transaction {i+1} error: {e}")
        
        return success_count > 0

    def wait_for_processing(self, seconds=10):
        """Ожидание обработки транзакций"""
        self.print_step(f"5. Ожидание обработки ({seconds} секунд)")
        print("   ⏳ Ожидаем обработки воркером...")
        time.sleep(seconds)

    def check_processed_transactions(self):
        """Проверка обработанных транзакций"""
        self.print_step("6. Проверка обработанных транзакций")
        
        try:
            response = requests.get(f"{BASE_URL}/api/admin/transactions", timeout=5)
            if response.status_code == 200:
                data = response.json()
                transactions = data.get("transactions", [])
                
                if transactions:
                    self.print_success(f"Найдено транзакций: {len(transactions)}")
                    
                    # Показываем статусы
                    status_count = {}
                    for tx in transactions:
                        status = tx.get("status", "unknown")
                        status_count[status] = status_count.get(status, 0) + 1
                    
                    for status, count in status_count.items():
                        self.print_success(f"  {status}: {count} транзакций")
                    
                    return True
                else:
                    self.print_warning("Нет транзакций в системе")
                    return False
            else:
                self.print_error(f"Failed to get transactions: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Transaction check error: {e}")
            return False

    def test_analytics(self):
        """Тест аналитики"""
        self.print_step("7. Проверка аналитики")
        
        try:
            response = requests.get(f"{BASE_URL}/api/admin/analytics", timeout=5)
            if response.status_code == 200:
                data = response.json()
                stats = data.get("stats", {})
                
                self.print_success("Analytics data:")
                for key, value in stats.items():
                    self.print_success(f"  {key}: {value}")
                
                return True
            else:
                self.print_error(f"Analytics failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Analytics error: {e}")
            return False

    def test_rules_management(self):
        """Тест управления правилами"""
        self.print_step("8. Проверка управления правилами")
        
        try:
            # Получить существующие правила
            response = requests.get(f"{BASE_URL}/api/admin/rules", timeout=5)
            if response.status_code == 200:
                data = response.json()
                rules = data.get("rules", [])
                
                self.print_success(f"Найдено правил: {len(rules)}")
                for rule in rules:
                    self.print_success(f"  {rule['name']} (активно: {rule['is_active']})")
                
                return True
            else:
                self.print_error(f"Rules check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Rules check error: {e}")
            return False

    def test_export(self):
        """Тест экспорта CSV"""
        self.print_step("9. Проверка экспорта CSV")
        
        try:
            response = requests.get(f"{BASE_URL}/api/export/transactions", timeout=10)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'text/csv' in content_type:
                    self.print_success("CSV export: OK")
                    # Сохраняем тестовый файл
                    with open('test_export.csv', 'wb') as f:
                        f.write(response.content)
                    self.print_success("Файл сохранен: test_export.csv")
                    return True
                else:
                    self.print_error(f"Wrong content type: {content_type}")
                    return False
            else:
                self.print_error(f"Export failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Export error: {e}")
            return False

    def test_api_documentation(self):
        """Тест документации API"""
        self.print_step("10. Проверка документации API")
        
        try:
            response = requests.get(f"{BASE_URL}/api/docs", timeout=5)
            if response.status_code == 200:
                self.print_success("Swagger documentation: OK")
                return True
            else:
                self.print_warning(f"Docs check: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_warning(f"Docs check error: {e}")
            return False

    async def run_full_test(self):
        """Запуск полного теста системы"""
        print("🚀 ЗАПУСК ПОЛНОЙ ПРОВЕРКИ ANTI-FRAUD СИСТЕМЫ")
        print("=" * 60)
        
        tests = [
            self.test_health,
            self.test_database_connection,
            self.test_redis_connection,
            self.create_test_transactions,
            lambda: self.wait_for_processing(8),  # Ждем обработки
            self.check_processed_transactions,
            self.test_analytics,
            self.test_rules_management,
            self.test_export,
            self.test_api_documentation
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if asyncio.iscoroutinefunction(test):
                    result = await test()
                else:
                    result = test()
                
                if result:
                    passed_tests += 1
            except Exception as e:
                self.print_error(f"Test crashed: {e}")
        
        # Итоги
        print("\n" + "=" * 60)
        print("🎯 ИТОГИ ТЕСТИРОВАНИЯ:")
        print(f"   Пройдено тестов: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print("   ✅ ВСЕ СИСТЕМЫ РАБОТАЮТ КОРРЕКТНО!")
        elif passed_tests >= total_tests * 0.7:
            print("   ⚠️  СИСТЕМА РАБОТАЕТ, ЕСТЬ НЕБОЛЬШИЕ ПРОБЛЕМЫ")
        else:
            print("   ❌ СИСТЕМА ТРЕБУЕТ ДОРАБОТКИ")
        
        print(f"\n📊 Для детальной проверки откройте: {BASE_URL}/api/docs")

def main():
    """Основная функция"""
    # Даем время на запуск контейнеров
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        print("⏳ Ожидаем запуск контейнеров...")
        time.sleep(15)
    
    tester = SystemTester()
    
    # Запускаем тесты
    try:
        asyncio.run(tester.run_full_test())
    except KeyboardInterrupt:
        print("\n🛑 Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
