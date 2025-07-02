
from flask import Flask, render_template_string, jsonify
from threading import Thread
import json
import os

app = Flask("")

# قراءة إعدادات البوت
def get_bot_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

@app.route("/")
def home():
    config = get_bot_config()
    
    html_template = """
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Echoes Act 1 Bot - WebView</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                color: white;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .status-badge {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                margin: 0 10px;
            }
            .online { background-color: #2ecc71; }
            .offline { background-color: #e74c3c; }
            .card {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .stat-card {
                background: rgba(255, 255, 255, 0.1);
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #f39c12;
            }
            .channel-list, .settings-list {
                list-style: none;
                padding: 0;
            }
            .channel-list li, .settings-list li {
                background: rgba(255, 255, 255, 0.05);
                margin: 5px 0;
                padding: 10px;
                border-radius: 5px;
                border-right: 4px solid #3498db;
            }
            .refresh-btn {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin: 10px;
            }
            .refresh-btn:hover {
                background: #2980b9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Echoes Act 1 Bot Dashboard</h1>
                <span class="status-badge {{ 'online' if bot_status else 'offline' }}">
                    {{ 'متصل ✅' if bot_status else 'غير متصل ❌' }}
                </span>
                <button class="refresh-btn" onclick="location.reload()">🔄 تحديث</button>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{{ registered_channels|length }}</div>
                    <div>رومات الرياكشن المسجلة</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ '1' if allowed_role else '0' }}</div>
                    <div>رتبة التحكم</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ 'نعم' if welcome_enabled else 'لا' }}</div>
                    <div>الترحيب مفعل</div>
                </div>
            </div>

            <div class="card">
                <h3>📋 رومات الرياكشن المسجلة</h3>
                {% if registered_channels %}
                    <ul class="channel-list">
                        {% for channel_id in registered_channels %}
                            <li>🟦 Channel ID: {{ channel_id }}</li>
                        {% endfor %}
                    </ul>
                {% else %}
                    <p>لا توجد رومات مسجلة</p>
                {% endif %}
            </div>

            <div class="card">
                <h3>🎯 إعدادات الترحيب</h3>
                <ul class="settings-list">
                    <li><strong>الروم:</strong> {{ welcome_channel if welcome_channel else 'غير محدد' }}</li>
                    <li><strong>الحالة:</strong> {{ 'مفعل ✅' if welcome_enabled else 'معطل ❌' }}</li>
                    <li><strong>رسالة الترحيب:</strong> {{ 'محددة ✅' if welcome_message else 'غير محددة ❌' }}</li>
                    <li><strong>رسالة خاصة:</strong> {{ 'محددة ✅' if dm_message else 'غير محددة ❌' }}</li>
                    <li><strong>صورة:</strong> {{ 'محددة ✅' if image_url else 'غير محددة ❌' }}</li>
                    <li><strong>خط زخرفي:</strong> {{ 'محدد ✅' if line_image else 'غير محدد ❌' }}</li>
                </ul>
            </div>

            <div class="card">
                <h3>ℹ️ معلومات النظام</h3>
                <p><strong>اسم البوت:</strong> Echoes Act 1</p>
                <p><strong>المنفذ:</strong> 8080</p>
                <p><strong>الحالة:</strong> يعمل 🟢</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template,
        bot_status=config.get('bot_status', False),
        registered_channels=config.get('registered_channels', []),
        allowed_role=config.get('allowed_role'),
        welcome_enabled=config.get('welcome_settings', {}).get('enabled', False),
        welcome_channel=config.get('welcome_settings', {}).get('channel_id'),
        welcome_message=config.get('welcome_settings', {}).get('message'),
        dm_message=config.get('welcome_settings', {}).get('dm_message'),
        image_url=config.get('welcome_settings', {}).get('image_url'),
        line_image=config.get('welcome_settings', {}).get('line_image_url')
    )

@app.route("/api/status")
def api_status():
    config = get_bot_config()
    return jsonify({
        'bot_status': config.get('bot_status', False),
        'registered_channels_count': len(config.get('registered_channels', [])),
        'welcome_enabled': config.get('welcome_settings', {}).get('enabled', False)
    })

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
  
