from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    html = '''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Телеграм Бот - Доставка</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { 
                background-color: #f8f9fa; 
                padding: 20px;
            }
            .container {
                max-width: 800px;
                background-color: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 0 15px rgba(0,0,0,0.1);
            }
            .feature-icon {
                font-size: 24px;
                margin-right: 10px;
            }
            .shop-section {
                margin-top: 30px;
                border-top: 1px solid #eee;
                padding-top: 20px;
            }
            .buff-card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                transition: all 0.3s;
            }
            .buff-card:hover {
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                transform: translateY(-3px);
            }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <div class="text-center mb-4">
                <h1>🚚 Телеграм Бот - Доставщик</h1>
                <p class="lead">Симулятор доставки с системой бонусов и магазином улучшений</p>
                <div class="alert alert-success">
                    <strong>✅ Статус:</strong> Бот работает!
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <h3>📋 Команды бота</h3>
                    <ul class="list-group">
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            /start
                            <span class="badge bg-primary rounded-pill">Начать использование</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            /raznos
                            <span class="badge bg-primary rounded-pill">Разносить посылки</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            /top
                            <span class="badge bg-primary rounded-pill">Таблица лидеров</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            /profile
                            <span class="badge bg-primary rounded-pill">Профиль курьера</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            /magaz
                            <span class="badge bg-primary rounded-pill">Магазин улучшений</span>
                        </li>
                    </ul>
                </div>
                
                <div class="col-md-6">
                    <h3>✨ Возможности</h3>
                    <div class="card mb-2">
                        <div class="card-body">
                            <span class="feature-icon">📦</span> Доставка посылок с рандомными наградами
                        </div>
                    </div>
                    <div class="card mb-2">
                        <div class="card-body">
                            <span class="feature-icon">🏆</span> Таблица лидеров с медалями
                        </div>
                    </div>
                    <div class="card mb-2">
                        <div class="card-body">
                            <span class="feature-icon">💰</span> Система бонусов за каждые 100 опыта
                        </div>
                    </div>
                    <div class="card mb-2">
                        <div class="card-body">
                            <span class="feature-icon">🔄</span> Кулдаун между доставками (2 минуты)
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-body">
                            <span class="feature-icon">🛒</span> Магазин с временными улучшениями
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="shop-section">
                <h3 class="text-center mb-4">🏪 Магазин улучшений</h3>
                <div class="row">
                    <div class="col-md-4">
                        <div class="buff-card">
                            <h5>Гипер Бафф</h5>
                            <p>Повышает доход на 50%</p>
                            <p>Длительность: 40 минут</p>
                            <p class="text-primary fw-bold">Цена: 2750 рублей</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="buff-card">
                            <h5>Супер Бафф</h5>
                            <p>Повышает доход на 15%</p>
                            <p>Длительность: 30 минут</p>
                            <p class="text-primary fw-bold">Цена: 850 рублей</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="buff-card">
                            <h5>Мега Бафф</h5>
                            <p>Повышает доход на 25%</p>
                            <p>Длительность: 30 минут</p>
                            <p class="text-primary fw-bold">Цена: 1800 рублей</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)