// Конфигурация
const API_BASE_URL = 'http://127.0.0.1:8000';

// Показ секций
function showSection(sectionName) {
    // Скрыть все секции
    document.getElementById('transactions-section').style.display = 'none';
    document.getElementById('rules-section').style.display = 'none';
    document.getElementById('analytics-section').style.display = 'none';
    
    // Показать выбранную секцию
    document.getElementById(`${sectionName}-section`).style.display = 'block';
    
    // Загрузить данные для секции
    switch(sectionName) {
        case 'transactions':
            loadTransactions();
            break;
        case 'rules':
            loadRules();
            break;
        case 'analytics':
            loadAnalytics();
            break;
    }
}

// Загрузка транзакций
async function loadTransactions() {
    const content = document.getElementById('transactions-content');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/transactions`);
        const data = await response.json();
        
        if (data.transactions && data.transactions.length > 0) {
            content.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Сумма</th>
                            <th>Валюта</th>
                            <th>Мерчант</th>
                            <th>User ID</th>
                            <th>Статус</th>
                            <th>Дата</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.transactions.map(tx => `
                            <tr>
                                <td>${tx.id}</td>
                                <td>${tx.amount}</td>
                                <td>${tx.currency}</td>
                                <td>${tx.merchant}</td>
                                <td>${tx.user_id}</td>
                                <td class="status-${tx.status}">${tx.status}</td>
                                <td>${new Date(tx.created_at).toLocaleString()}</td>
                                <td>
                                    <button onclick="viewTransaction('${tx.id}')">Просмотр</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            content.innerHTML = '<p>Нет транзакций</p>';
        }
    } catch (error) {
        content.innerHTML = `<div class="error">Ошибка загрузки: ${error.message}</div>`;
    }
}

// Просмотр деталей транзакции
async function viewTransaction(transactionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/transactions/${transactionId}`);
        const data = await response.json();
        
        alert(`
Детали транзакции:
ID: ${data.transaction.id}
Сумма: ${data.transaction.amount} ${data.transaction.currency}
Мерчант: ${data.transaction.merchant}
Статус: ${data.transaction.status}
User ID: ${data.transaction.user_id}
Дата: ${new Date(data.transaction.created_at).toLocaleString()}

Результаты правил:
${data.rule_results.map(rule => `
Правило ${rule.rule_id}: 
  Сработало: ${rule.triggered ? 'Да' : 'Нет'}
  Риск: ${rule.risk_score}
  Детали: ${rule.details || 'Нет'}
`).join('')}
        `);
    } catch (error) {
        alert(`Ошибка загрузки деталей: ${error.message}`);
    }
}

// Загрузка правил
async function loadRules() {
    const content = document.getElementById('rules-content');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/rules`);
        const data = await response.json();
        
        if (data.rules && data.rules.length > 0) {
            content.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Название</th>
                            <th>Описание</th>
                            <th>Тип</th>
                            <th>Риск</th>
                            <th>Активно</th>
                            <th>Приоритет</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.rules.map(rule => `
                            <tr>
                                <td>${rule.id}</td>
                                <td>${rule.name}</td>
                                <td>${rule.description}</td>
                                <td>${rule.type}</td>
                                <td>${rule.risk_score}</td>
                                <td>${rule.is_active ? 'Да' : 'Нет'}</td>
                                <td>${rule.priority}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            content.innerHTML = '<p>Нет правил</p>';
        }
    } catch (error) {
        content.innerHTML = `<div class="error">Ошибка загрузки: ${error.message}</div>`;
    }
}

// Форма создания правила
function showCreateRuleForm() {
    const formHtml = `
        <div style="margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 4px;">
            <h3>Создать новое правило</h3>
            <form onsubmit="createRule(event)">
                <div style="margin: 10px 0;">
                    <input type="text" name="name" placeholder="Название правила" required style="width: 100%; padding: 8px;">
                </div>
                <div style="margin: 10px 0;">
                    <textarea name="description" placeholder="Описание" style="width: 100%; padding: 8px; height: 60px;"></textarea>
                </div>
                <div style="margin: 10px 0;">
                    <input type="text" name="type" placeholder="Тип" required style="width: 100%; padding: 8px;">
                </div>
                <div style="margin: 10px 0;">
                    <textarea name="condition" placeholder="Условие (JSON)" required style="width: 100%; padding: 8px; height: 100px;"></textarea>
                </div>
                <div style="margin: 10px 0;">
                    <input type="number" name="risk_score" placeholder="Оценка риска" required style="width: 100%; padding: 8px;">
                </div>
                <div style="margin: 10px 0;">
                    <label>
                        <input type="checkbox" name="is_active" checked> Активно
                    </label>
                </div>
                <div style="margin: 10px 0;">
                    <input type="number" name="priority" placeholder="Приоритет" required style="width: 100%; padding: 8px;">
                </div>
                <button type="submit" style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 4px;">Создать</button>
                <button type="button" onclick="loadRules()" style="padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 4px;">Отмена</button>
            </form>
        </div>
    `;
    
    document.getElementById('rules-content').innerHTML = formHtml + document.getElementById('rules-content').innerHTML;
}

// Создание правила
async function createRule(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const ruleData = {
        name: formData.get('name'),
        description: formData.get('description'),
        type: formData.get('type'),
        condition: JSON.parse(formData.get('condition')),
        risk_score: parseInt(formData.get('risk_score')),
        is_active: formData.get('is_active') === 'on',
        priority: parseInt(formData.get('priority'))
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/rules`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(ruleData)
        });
        
        if (response.ok) {
            alert('Правило успешно создано!');
            loadRules();
        } else {
            const error = await response.json();
            alert(`Ошибка: ${error.detail}`);
        }
    } catch (error) {
        alert(`Ошибка: ${error.message}`);
    }
}

// Загрузка аналитики
async function loadAnalytics() {
    const content = document.getElementById('analytics-content');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/analytics`);
        const data = await response.json();
        
        let html = '<h3>Статистика</h3>';
        
        if (data.stats) {
            html += `
                <p>Всего транзакций: ${data.stats.total_transactions || 0}</p>
                <p>Одобрено: ${data.stats.approved_transactions || 0}</p>
                <p>Отклонено: ${data.stats.declined_transactions || 0}</p>
            `;
        }
        
        if (data.hourly_data) {
            html += '<h3>Транзакции по часам</h3>';
            data.hourly_data.forEach(hour => {
                html += `<p>Час ${hour.hour}: ${hour.count} транзакций</p>`;
            });
        }
        
        content.innerHTML = html;
    } catch (error) {
        content.innerHTML = `<div class="error">Ошибка загрузки: ${error.message}</div>`;
    }
}

// Экспорт транзакций
async function exportTransactions() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/export/transactions`);
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'transactions.csv';
        
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        alert(`Ошибка экспорта: ${error.message}`);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    loadTransactions();
});