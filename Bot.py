import os
import sqlite3
import time
import random
import logging
import secrets
from threading import Thread

from dotenv import load_dotenv
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("anonchat")

VK_TOKEN = os.getenv("VK_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")

if not VK_TOKEN or not VK_GROUP_ID:
    log.error("Не заданы VK_TOKEN и/или VK_GROUP_ID в .env")
    raise SystemExit(1)

try:
    VK_GROUP_ID = int(VK_GROUP_ID)
except ValueError:
    log.error("VK_GROUP_ID должен быть числом")
    raise SystemExit(1)

# секретный ключ (для будущего)
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(32)
    with open(".env", "a") as f:
        f.write(f"\nSECRET_KEY={SECRET_KEY}")
    log.info("Сгенерирован новый SECRET_KEY")

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID, wait=25)

DB_PATH = "anonchat.db"

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                status TEXT NOT NULL,
                room_id INTEGER
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                a INTEGER NOT NULL,
                b INTEGER NOT NULL
            )
        """)
        con.commit()

def db_execute(query, params=(), fetch=False, many=False):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        if many:
            cur.executemany(query, params)
            con.commit()
            return None
        cur.execute(query, params)
        if fetch:
            return cur.fetchall()
        con.commit()
        return None

def send(user_id, text):
    try:
        vk.messages.send(
            peer_id=user_id,
            message=text,
            random_id=random.randint(1, 2**31 - 1)
        )
        time.sleep(0.035)
    except Exception as e:
        log.exception("Ошибка отправки: %s", e)

def find_waiting(exclude_id):
    rows = db_execute(
        "SELECT user_id FROM users WHERE status = 'waiting' AND user_id != ? LIMIT 1",
        (exclude_id,),
        fetch=True
    )
    return rows[0][0] if rows else None

def set_user_status(user_id, status, room_id=None):
    db_execute(
        "INSERT OR REPLACE INTO users(user_id, status, room_id) VALUES(?, ?, ?)",
        (user_id, status, room_id)
    )

def create_room(a, b):
    db_execute("INSERT INTO rooms(a, b) VALUES(?, ?)", (a, b))
    rows = db_execute(
        "SELECT id FROM rooms WHERE a=? AND b=? ORDER BY id DESC LIMIT 1",
        (a, b),
        fetch=True
    )
    return rows[0][0]

def delete_room(room_id):
    db_execute("DELETE FROM rooms WHERE id = ?", (room_id,))
    db_execute(
        "UPDATE users SET status='idle', room_id=NULL WHERE room_id = ?",
        (room_id,)
    )

def get_partner(user_id):
    rows = db_execute(
        "SELECT room_id FROM users WHERE user_id = ?",
        (user_id,),
        fetch=True
    )
    if not rows or not rows[0][0]:
        return None
    room_id = rows[0][0]
    rows = db_execute(
        "SELECT a, b FROM rooms WHERE id = ?",
        (room_id,),
        fetch=True
    )
    if not rows:
        return None
    a, b = rows[0]
    return b if a == user_id else a

def start_chat(user_id):
    partner = find_waiting(user_id)
    if partner:
        room_id = create_room(user_id, partner)
        set_user_status(user_id, "chatting", room_id)
        set_user_status(partner, "chatting", room_id)
        msg = "Вы подключены к анонимному собеседнику.\nНапишите сообщение. /stop — завершить, /next — новый собеседник."
        send(user_id, msg)
        send(partner, msg)
        log.info("Пара %s и %s в комнате %s", user_id, partner, room_id)
    else:
        set_user_status(user_id, "waiting", None)
        send(user_id, "Вы поставлены в очередь ожидания. /stop чтобы выйти.")
        log.info("Пользователь %s в очереди", user_id)

def stop_chat(user_id):
    rows = db_execute(
        "SELECT status, room_id FROM users WHERE user_id = ?",
        (user_id,),
        fetch=True
    )
    if not rows:
        send(user_id, "Вы не в чате и не в очереди.")
        return
    status, room_id = rows[0]
    if status == "waiting":
        db_execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        send(user_id, "Вы вышли из очереди.")
        return
    if status == "chatting" and room_id:
        partner = get_partner(user_id)
        delete_room(room_id)
        if partner:
            send(partner, "Собеседник завершил диалог.")
        send(user_id, "Диалог завершён.")
        log.info("Комната %s закрыта", room_id)
        return
    send(user_id, "Нет активного диалога.")

def next_chat(user_id):
    stop_chat(user_id)
    start_chat(user_id)

def handle_text(user_id, text):
    t = text.strip().lower()
    if t in ("/start", "start", "начать"):
        start_chat(user_id)
        return
    if t in ("/stop", "stop", "стоп", "выйти"):
        stop_chat(user_id)
        return
    if t in ("/next", "далее", "следующий"):
        next_chat(user_id)
        return
    if t in ("/help", "помощь"):
        send(user_id, "Команды: /start, /stop, /next, /help")
        return
    partner = get_partner(user_id)
    if not partner:
        send(user_id, "Вы не подключены. Напишите /start.")
        return
    send(partner, text)

def event_listener():
    log.info("Запуск прослушивания...")
    for event in longpoll.listen():
        try:
            if event.type == VkBotEventType.MESSAGE_NEW:
                msg = event.object.get("message") or event.message
                from_id = msg.get("from_id")
                text = msg.get("text", "")
                if from_id == -VK_GROUP_ID or from_id is None:
                    continue
                log.info("Сообщение от %s: %s", from_id, text)
                handle_text(from_id, text)
        except Exception as e:
            log.exception("Ошибка: %s", e)
            time.sleep(1)

def main():
    init_db()
    log.info("База данных инициализирована.")
    Thread(target=event_listener, daemon=True).start()
    log.info("Бот запущен. Нажмите Ctrl+C для остановки.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Остановка...")

if __name__ == "__main__":
    main()