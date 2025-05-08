import csv
import json
from tkinter import simpledialog
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
from telethon.tl.functions.messages import GetHistoryRequest


def telegram_connect(api_id, api_hash, root):
    print("Подключение к Telegram...")
    client = TelegramClient(
        'session', api_id, api_hash,
        device_model="Parser Desktop",
        system_version="Windows 10",
        app_version="TelegramClient 1.0",
        lang_code="ru",
        system_lang_code="ru"
    )

    try:
        client.connect()
        if not client.is_user_authorized():
            print("Требуется авторизация.")
            phone = simpledialog.askstring("Авторизация Telegram", "Введите номер телефона (в формате +7XXXXXXXXXX):",
                                           parent=root)
            if not phone:
                raise Exception("Ввод номера телефона отменен")

            client.send_code_request(phone)

            code = simpledialog.askstring("Авторизация Telegram", "Введите код:", parent=root)
            if not code:
                raise Exception("Ввод кода отменен")

            try:
                client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = simpledialog.askstring("Двухфакторная защита", "Введите пароль:", show="*", parent=root)
                if not password:
                    raise Exception("Ввод пароля отменен")
                client.sign_in(password=password)
            print("Авторизация прошла успешно!")
        else:
            print("Вы уже авторизованы!")
    except PhoneCodeInvalidError:
        print("Ошибка: неверный код.")
        client.disconnect()
        raise Exception("Неверный код авторизации")
    except PhoneCodeExpiredError:
        print("Ошибка: код истек.")
        client.disconnect()
        raise Exception("Код авторизации истек")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        client.disconnect()
        raise Exception(f"Ошибка подключения: {e}")

    if client.is_connected():
        print("Telegram клиент подключен.")
        return client
    else:
        print("Не удалось подключиться к Telegram.")
        raise Exception("Не удалось подключиться к Telegram")


def fetch_telegram_posts(client, channel_name, limit=100):
    try:
        entity = client.get_entity(channel_name)
        history = client(GetHistoryRequest(
            peer=entity,
            offset_id=0,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))
        messages = [{'date': msg.date.strftime('%Y-%m-%d %H:%M:%S'), 'text': msg.message}
                    for msg in history.messages if msg.message]
        return messages
    except Exception as e:
        print(f"Ошибка при получении сообщений: {e}")
        return []


def save_to_csv(messages, filename='telegram_posts.csv'):
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['date', 'text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for msg in messages:
                writer.writerow(msg)
        print(f"Сообщения успешно сохранены в файл {filename}.")
    except Exception as e:
        print(f"Ошибка при сохранении в CSV: {e}")


def fetch_chat_history(client, chat_name, limit=None):
    messages = []
    try:
        chat = client.get_entity(chat_name)
        for message in client.iter_messages(chat, limit=limit):
            messages.append({
                "id": message.id,
                "date": message.date.strftime('%Y-%m-%d %H:%M:%S'),
                "sender_id": message.sender_id,
                "text": message.text
            })
        return messages
    except Exception as e:
        print(f"Ошибка при скачивании сообщений: {e}")
        raise Exception(f"Ошибка при получении сообщений: {e}")