import json
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError

# Введите свои данные API
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
        # Пытаемся подключиться к клиенту
        client.connect()

        # Если пользователь не авторизован, запрашиваем вход
        if not client.is_user_authorized():
            print("Требуется авторизация.")
            phone = input("Введите номер телефона (в формате +7XXXXXXXXXX): ")
            try:
                client.send_code_request(phone)  # Отправляем код авторизации
                code = input("Введите код, который пришел в Telegram: ")
                try:
                    # Пробуем авторизоваться с введенным кодом
                    client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    # Если требуется двухфакторный пароль, запрашиваем его
                    password = input("Введите пароль двухфакторной защиты: ")
                    client.sign_in(password=password)
                print("Авторизация прошла успешно!")
            except PhoneCodeInvalidError:
                print("Ошибка: введен неверный код. Попробуйте снова.")
                exit()
            except PhoneCodeExpiredError:
                print("Ошибка: код истек. Запросите новый код.")
                exit()
        else:
            print("Вы уже авторизованы!")

    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        if client.is_connected():
            print("Telegram клиент подключен.")
            return client

    # После авторизации
    if client.is_user_authorized():
        print("Вы вошли в аккаунт Telegram!")
        return client
    else:
        print("Не удалось войти в аккаунт.")
        client.disconnect()
        exit()


def fetch_chat_history(client, chat_name, limit=100):
    """Функция для получения истории переписки"""
    messages = []

    # Поиск чата по имени/ID
    print(f"Ищем чат: {chat_name}...")
    try:
        chat = client.get_entity(chat_name)
    except Exception as e:
        print(f"Ошибка при поиске чата: {e}")
        return []

    # Итерация по сообщениям
    print(f"Скачиваем сообщения из чата: {chat_name}...")
    try:
        for message in client.iter_messages(chat, limit=limit):
            messages.append({
                "id": message.id,
                "date": str(message.date),
                "sender_id": message.sender_id,
                "text": message.text
            })
    except Exception as e:
        print(f"Ошибка при скачивании сообщений: {e}")
        return []

    # Сохранение в JSON
    try:
        with open('telegram_chat_history.json', 'w', encoding='utf-8') as file:
            json.dump(messages, file, ensure_ascii=False, indent=4)
        print("Сообщения успешно сохранены в файл telegram_chat_history.json.")
    except Exception as e:
        print(f"Ошибка при сохранении в файл: {e}")

    return messages

# def example():
#     client = telegram_connect(api_id, api_hash)
#     # Введите ID или имя чата
#     chat_name = input("Введите ID, имя пользователя или ссылку на чат: ")
#
#     # Получение и вывод сообщений
#     history = fetch_chat_history(client, chat_name, limit=100)
#     print(json.dumps(history, ensure_ascii=False, indent=4))
#
#     # Отключение клиента
#     client.disconnect()
#     print("Сессия завершена.")

# example()