import tkinter as tk
from parse_from_vkontakte import get_user_id, get_full_conversation
from tkinter import filedialog
from tkinter import ttk
from parse_from_telegram import telegram_connect, fetch_chat_history
import json

def save_file():
    folder = filedialog.askdirectory()
    if folder:
        path_label.config(text=folder)

def toggle_token_visibility(entry, button):
    # Переключение отображения текста/звездочек для любого текстбокса
    if entry.cget("show") == "*":
        entry.config(show="")
        button.config(text="Скрыть")
    else:
        entry.config(show="*")
        button.config(text="Показать")

def parse_from_vk():
    username = id_entry.get()
    access_token = token_entry.get()
    user_id = get_user_id(username, access_token)

    conversation = get_full_conversation(user_id, access_token)
    with open("conversation_vk.json", "w", encoding="utf-8") as f:
        json.dump(conversation, f, ensure_ascii=False, indent=4)

def parse_from_telegram():
    chat_name = id_entry.get()
    api_id = token_entry.get()
    api_hash = api_hash_entry.get()
    client = telegram_connect(api_id, api_hash)
    chat_history = fetch_chat_history(client, chat_name)
    with open("conversation_telegram.json", "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=4)

def start_parsing():
    selected_platform = platform_var.get()
    if selected_platform == "ВКонтакте":
        parse_from_vk()
    elif selected_platform == "Телеграм":
        parse_from_telegram()

def on_platform_change(event):
    selected_platform = platform_var.get()
    if selected_platform == "Телеграм":
        # Показываем лейбл и текстбокс для API hash
        api_hash_label.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        api_hash_entry.grid(row=3, column=0, padx=20, pady=5)
        show_hash_button.grid(row=3, column=1, padx=10, pady=5)
        token_label.config(text="Введите API ID")  # Меняем заголовок для первого поля
    else:
        # Скрываем лейбл и текстбокс для API hash
        api_hash_label.grid_remove()
        api_hash_entry.grid_remove()
        show_hash_button.grid_remove()
        token_label.config(text="Введите API токен")  # Восстанавливаем заголовок

# Создаем основное окно
root = tk.Tk()
root.title("Парсер данных")
root.geometry("600x500")
root.configure(bg="lightgray")

# Поле ввода для API токена (или API ID)
token_label = tk.Label(root, text="Введите API токен", bg="lightgray")
token_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

token_entry = tk.Entry(root, width=40, show="*", font=("Arial", 14))
token_entry.grid(row=1, column=0, padx=20, pady=5)

show_token_button = tk.Button(root, text="Показать", command=lambda: toggle_token_visibility(token_entry, show_token_button))
show_token_button.grid(row=1, column=1, padx=10, pady=5)

# Лейбл и текстбокс для API hash (скрыты по умолчанию)
api_hash_label = tk.Label(root, text="Введите API hash", bg="lightgray")
api_hash_entry = tk.Entry(root, width=40, show="*", font=("Arial", 14))
show_hash_button = tk.Button(root, text="Показать", command=lambda: toggle_token_visibility(api_hash_entry, show_hash_button))

# Выпадающий список для выбора платформы
platform_label = tk.Label(root, text="Выберите платформу", bg="lightgray")
platform_label.grid(row=4, column=0, padx=20, pady=5, sticky="w")

platform_var = tk.StringVar()
platform_combobox = ttk.Combobox(root, textvariable=platform_var, values=["ВКонтакте", "Телеграм", "WebSite"], state="readonly", width=37)
platform_combobox.grid(row=5, column=0, padx=20, pady=5)
platform_combobox.current(0)
platform_combobox.bind("<<ComboboxSelected>>", on_platform_change)

# Поле для ссылки/ID собеседника
id_label = tk.Label(root, text="Введите ID собеседника или ссылку", bg="lightgray")
id_label.grid(row=6, column=0, padx=20, pady=5, sticky="w")

id_entry = tk.Entry(root, width=40)
id_entry.grid(row=7, column=0, padx=20, pady=5)

# Кнопка для выбора пути сохранения
save_label = tk.Label(root, text="Выберите место, куда сохранить текст", bg="lightgray")
save_label.grid(row=8, column=0, padx=20, pady=5, sticky="w")

path_label = tk.Label(root, text="", bg="lightgray")
path_label.grid(row=9, column=0, padx=20, pady=5, sticky="w")

save_button = tk.Button(root, text="...", command=save_file)
save_button.grid(row=9, column=1, padx=10, pady=5)

# Кнопка запуска
start_button = tk.Button(root, text="Пуск", width=10, command=start_parsing)
start_button.grid(row=10, column=1, padx=10, pady=20, sticky="e")

root.mainloop()
