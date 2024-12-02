import csv
import json
from tkinter import simpledialog

from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
from telethon.tl.functions.messages import GetHistoryRequest


# Функция подключения к Telegram
def telegram_connect(api_id, api_hash):
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
        client.connect()  # Подключение к Telegram

        # Если пользователь не авторизован, запускаем процесс авторизации
        if not client.is_user_authorized():
            print("Требуется авторизация.")

            # Ввод номера телефона
            phone = simpledialog.askstring(
                "Авторизация Telegram",
                "Введите номер телефона (в формате +7XXXXXXXXXX):",
                parent=None
            )
            client.send_code_request(phone)  # Отправляем код авторизации

            # Ввод кода авторизации
            code = simpledialog.askstring(
                "Авторизация Telegram",
                "Введите код, который пришел в Telegram:",
                parent=None
            )
            try:
                client.sign_in(phone, code)  # Авторизация с кодом
            except SessionPasswordNeededError:
                # Если требуется двухфакторная защита, запрос пароля
                password = simpledialog.askstring(
                    "Двухфакторная защита",
                    "Введите пароль двухфакторной авторизации:",
                    show="*",  # Скрываем вводимые символы
                    parent=None
                )
                client.sign_in(password=password)

            print("Авторизация прошла успешно!")
        else:
            print("Вы уже авторизованы!")

    except PhoneCodeInvalidError:
        print("Ошибка: неверный код. Попробуйте снова.")
        client.disconnect()
        exit()
    except PhoneCodeExpiredError:
        print("Ошибка: код истек. Запросите новый код.")
        client.disconnect()
        exit()
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        client.disconnect()
        exit()

    if client.is_connected():
        print("Telegram клиент подключен.")
        return client
    else:
        print("Не удалось подключиться к Telegram.")
        exit()


# Функция для получения постов из канала
def fetch_telegram_posts(client, channel_name, limit=100):
    try:
        # Получаем объект канала
        entity = client.get_entity(channel_name)

        # Получаем историю сообщений
        history = client(GetHistoryRequest(
            peer=entity,
            offset_id=0,
            offset_date=None,
            add_offset=0,
            limit=limit,  # Количество сообщений
            max_id=0,
            min_id=0,
            hash=0
        ))

        messages = []
        for message in history.messages:
            if message.message:  # Учитываем только текстовые сообщения
                messages.append({
                    'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                    'text': message.message
                })

        return messages

    except Exception as e:
        print(f"Ошибка при получении сообщений: {e}")
        return []


# Сохранение сообщений в CSV
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


# Функция для получения истории переписки
def fetch_chat_history(client, chat_name, limit=100):
    messages = []

    print(f"Ищем чат: {chat_name}...")
    try:
        chat = client.get_entity(chat_name)
    except Exception as e:
        print(f"Ошибка при поиске чата: {e}")
        return []

    print(f"Скачиваем сообщения из чата: {chat_name}...")
    try:
        for message in client.iter_messages(chat, limit=limit):
            messages.append({
                "id": message.id,
                "date": message.date.strftime('%Y-%m-%d %H:%M:%S'),
                "sender_id": message.sender_id,
                "text": message.text
            })

        # Сохранение в JSON
        with open('telegram_chat_history.json', 'w', encoding='utf-8') as file:
            json.dump(messages, file, ensure_ascii=False, indent=4)

        print("Сообщения успешно сохранены в файл telegram_chat_history.json.")
    except Exception as e:
        print(f"Ошибка при скачивании сообщений: {e}")

    return messages