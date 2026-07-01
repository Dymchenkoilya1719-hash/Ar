# Ar - Анонимный ЧАТ БОТ для ВК

Бот для анонимного общения в ВКонтакте. Пользователи могут подключаться друг к другу через бота и общаться анонимно.

## 🎯 Функции

- 👥 Анонимное соединение случайных пользователей
- 💬 Чат с собеседником
- 🔄 Смена собеседника (команда `/next`)
- 🛑 Выход из чата (команда `/stop`)
- 📊 Сохранение статуса пользователей в БД (SQLite)

## 📋 Требования

- Python 3.8+
- ВК токен группы/бота
- ID группы ВК

## ⚙️ Установка

### 1. Локально

```bash
# Клонирование репозитория
git clone https://github.com/Dymchenkoilya1719-hash/Ar.git
cd Ar

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Настройка .env

Переименуйте `env.` в `.env` и укажите ваши данные:

```env
VK_TOKEN=ваш_токен_группы_вк
VK_GROUP_ID=id_вашей_группы
SECRET_KEY=автоматически_сгенерируется
```

## 🚀 Запуск

### Локально
```bash
python Bot.py
```

### Docker
```bash
docker build -t anonbot .
docker run -d --name anonbot anonbot
```

### GitHub Actions (автоматический деплой)
При каждом пушe в main ветку бот автоматически перестартует.

## 📦 Развертывание на хост

### Вариант 1: На собственном сервере (VPS)

```bash
# SSH в сервер
ssh user@your_server

# Клонируем репо
git clone https://github.com/Dymchenkoilya1719-hash/Ar.git
cd Ar

# Устанавливаем зависимости
pip install -r requirements.txt

# Запускаем в фоне (tmux или screen)
tmux new-session -d -s anonbot "python Bot.py"

# Или systemd сервис:
sudo nano /etc/systemd/system/anonbot.service
```

**Содержимое systemd сервиса:**
```ini
[Unit]
Description=VK Anonymous Chat Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/Ar
ExecStart=/usr/bin/python3 /path/to/Ar/Bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable anonbot
sudo systemctl start anonbot
```

### Вариант 2: На Render.com (PaaS)

1. Подключите репозиторий к Render.com
2. Создайте новый Background Worker
3. Установите переменные окружения (VK_TOKEN, VK_GROUP_ID)
4. Выберите `python Bot.py` как команду запуска

### Вариант 3: На Heroku (классический вариант)

```bash
# Установите Heroku CLI
heroku login
heroku create your-app-name
heroku config:set VK_TOKEN=your_token VK_GROUP_ID=your_id
git push heroku main
```

### Вариант 4: На GitHub Codespaces (для тестирования)

```bash
# В Codespaces терминал
pip install -r requirements.txt
python Bot.py
```

## 🔧 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начать поиск собеседника |
| `/stop` | Завершить чат |
| `/next` | Перейти к новому собеседнику |
| `/help` | Помощь и список команд |

## 📂 Структура файлов

```
Ar/
├── Bot.py              # Главный файл бота
├── requirements.txt    # Зависимости Python
├── Dockerfile          # Docker конфиг
├── .env                # Переменные окружения (не коммитить!)
├── .gitignore          # Git игнор файлы
└── README.md           # Документация
```

## 🔒 Безопасность

⚠️ **ВАЖНО**: Не коммитьте `.env` файл с реальными токенами!

Используйте GitHub Secrets для CI/CD:
```bash
# Добавить секреты в репо
Settings → Secrets → New repository secret
- VK_TOKEN
- VK_GROUP_ID
```

## 📝 Логирование

Бот логирует все события:
- Подключение к БД
- Новые пары пользователей
- Смену статусов
- Ошибки при отправке сообщений

## 🆘 Решение проблем

**Ошибка: "Не заданы VK_TOKEN и/или VK_GROUP_ID"**
→ Проверьте наличие и правильность файла `.env`

**БД не создается**
→ Проверьте права доступа в папке, бот должен иметь право на запись

**Бот не отвечает на команды**
→ Проверьте VK_TOKEN в консоли ВК разработчика
→ Убедитесь, что группа активирована как бот

## 📄 Лицензия

MIT License - используйте свободно!

## 👨‍💻 Автор

Dymchenkoilya1719-hash

---

**Готово к деплою!** 🚀