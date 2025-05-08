import asyncio
from telethon import TelegramClient
import tkinter as tk
from tkinter import simpledialog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def ask_input(root, title, prompt, show=None):
    future = asyncio.Future()
    def callback():
        result = simpledialog.askstring(title, prompt, parent=root, show=show)
        future.set_result(result)
    root.after(0, callback)
    return await future

async def telegram_connect(api_id, api_hash, root):
    client = TelegramClient('session', api_id, api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            while True:
                phone = await ask_input(root, "Телефон", "Введите номер телефона:")
                if phone:
                    break
                root.after(0, lambda: simpledialog.messagebox.showwarning("Предупреждение", "Номер телефона обязателен!"))
            await client.send_code_request(phone)
            while True:
                code = await ask_input(root, "Код", "Введите код из Telegram:")
                if code:
                    break
                root.after(0, lambda: simpledialog.messagebox.showwarning("Предупреждение", "Код обязателен!"))
            try:
                await client.sign_in(phone, code)
            except Exception as e:
                if "Two-steps verification" in str(e):
                    while True:
                        password = await ask_input(root, "Пароль", "Введите пароль:", show="*")
                        if password:
                            break
                        root.after(0, lambda: simpledialog.messagebox.showwarning("Предупреждение", "Пароль обязателен!"))
                    await client.sign_in(password=password)
                else:
                    raise e
        return client
    except Exception as e:
        logger.error(f"Ошибка подключения к Telegram: {e}")
        await client.disconnect()
        return None

async def fetch_chat_history(client, chat_name, update_progress=None):
    if not client:
        return None, "Не удалось подключиться к Telegram"

    try:
        chat = await client.get_entity(chat_name)
        total_messages = (await client.get_messages(chat, limit=0)).total
        if total_messages == 0:
            return [], "Чат пуст"

        messages = []
        async for message in client.iter_messages(chat, limit=None):
            msg_data = {
                'id': message.id,
                'date': str(message.date),
                'text': message.text,
                'sender_id': message.sender_id
            }
            messages.append(msg_data)
            if update_progress and total_messages:
                update_progress(len(messages), total_messages)

        return messages, None
    except Exception as e:
        logger.error(f"Ошибка получения сообщений: {e}")
        return None, f"Ошибка получения сообщений: {e}"