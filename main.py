import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
import os
from threading import Thread
from parse_messages_from_vkontakte import get_user_id, get_full_conversation, get_user_posts_in_groups
from parse_messages_from_telegram import telegram_connect, fetch_chat_history

# Глобальные переменные
save_folder = ""
progress_bar = None
is_parsing = False
status_label = None

def save_file():
    global save_folder
    save_folder = filedialog.askdirectory()
    if save_folder:
        path_label.config(text=save_folder)

def toggle_token_visibility(entry, button):
    if entry.cget("show") == "*":
        entry.config(show="")
        button.config(text="Скрыть")
    else:
        entry.config(show="*")
        button.config(text="Показать")

def update_progress(current, total):
    if progress_bar:
        progress_bar['value'] = (current / total) * 100
        root.update_idletasks()

def set_ui_state(enabled):
    """Включает или отключает элементы интерфейса"""
    state = 'normal' if enabled else 'disabled'
    start_button.config(state=state)
    save_button.config(state=state)
    token_entry.config(state=state)
    id_entry.config(state=state)
    platform_combobox.config(state=state)
    parse_type_combobox.config(state=state)
    show_token_button.config(state=state)
    if platform_var.get() == "Телеграм":
        api_hash_entry.config(state=state)
        show_hash_button.config(state=state)

def update_status(text):
    """Обновляет текст состояния"""
    if status_label:
        status_label.config(text=text)
        root.update_idletasks()

def parse_from_vk():
    global save_folder, progress_bar, is_parsing
    if not save_folder:
        messagebox.showerror("Ошибка", "Выберите папку для сохранения!")
        return

    username = id_entry.get()
    access_token = token_entry.get()
    if not username or not access_token:
        messagebox.showerror("Ошибка", "Введите имя пользователя и токен!")
        return

    user_id = get_user_id(username, access_token)
    if not user_id:
        return

    is_parsing = True
    set_ui_state(False)
    update_status("Идёт парсинг...")
    progress_bar['value'] = 0

    if parse_type_var.get() == "Сообщения":
        data, error = get_full_conversation(user_id, access_token, update_progress)
        if error:
            messagebox.showerror("Ошибка", error)
            is_parsing = False
            set_ui_state(True)
            update_status("")
            return
        filename = f"conversation_vk_{username}.json"
    else:
        data = get_user_posts_in_groups(user_id, access_token, update_progress=update_progress)
        filename = f"vk_user_posts_{username}.json"

    save_path = os.path.join(save_folder, filename)
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Данные ВКонтакте сохранены в {save_path}")
        messagebox.showinfo("Успех", f"Данные сохранены в {save_path}")
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")
    finally:
        progress_bar['value'] = 100
        is_parsing = False
        set_ui_state(True)
        update_status("")

def parse_from_telegram():
    global save_folder, progress_bar, is_parsing
    if not save_folder:
        messagebox.showerror("Ошибка", "Выберите папку для сохранения!")
        return

    chat_name = id_entry.get()
    api_id = token_entry.get()
    api_hash = api_hash_entry.get()
    if not all([chat_name, api_id, api_hash]):
        messagebox.showerror("Ошибка", "Заполните все поля!")
        return

    is_parsing = True
    set_ui_state(False)
    update_status("Идёт парсинг...")
    progress_bar['value'] = 0

    client = telegram_connect(api_id, api_hash)
    chat_history = fetch_chat_history(client, chat_name)
    save_path = os.path.join(save_folder, f"conversation_telegram_{chat_name}.json")
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=4)
        print(f"Данные Telegram сохранены в {save_path}")
        messagebox.showinfo("Успех", f"Данные сохранены в {save_path}")
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")
    finally:
        progress_bar['value'] = 100
        is_parsing = False
        set_ui_state(True)
        update_status("")

def start_parsing():
    global is_parsing
    if is_parsing:
        messagebox.showwarning("Предупреждение", "Дождитесь завершения текущей операции!")
        return

    platform = platform_var.get()
    thread = Thread(target=parse_from_vk if platform == "ВКонтакте" else parse_from_telegram)
    thread.start()

def on_platform_change(event):
    platform = platform_var.get()
    if platform == "Телеграм":
        api_hash_label.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        api_hash_entry.grid(row=3, column=0, padx=20, pady=5)
        show_hash_button.grid(row=3, column=1, padx=10, pady=5)
        token_label.config(text="Введите API ID")
        parse_type_label.grid_remove()
        parse_type_combobox.grid_remove()
    else:
        api_hash_label.grid_remove()
        api_hash_entry.grid_remove()
        show_hash_button.grid_remove()
        token_label.config(text="Введите API токен")
        parse_type_label.grid(row=6, column=0, padx=20, pady=5, sticky="w")
        parse_type_combobox.grid(row=7, column=0, padx=20, pady=5)

# Создаем основное окно
root = tk.Tk()
root.title("Парсер данных")
root.geometry("600x570")  # Увеличиваем высоту для метки состояния
root.configure(bg="lightgray")

# Поле ввода для API токена (или API ID)
token_label = tk.Label(root, text="Введите API токен", bg="lightgray")
token_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

token_entry = tk.Entry(root, width=40, show="*", font=("Arial", 14))
token_entry.grid(row=1, column=0, padx=20, pady=5)

show_token_button = tk.Button(root, text="Показать", command=lambda: toggle_token_visibility(token_entry, show_token_button))
show_token_button.grid(row=1, column=1, padx=10, pady=5)

api_hash_label = tk.Label(root, text="Введите API hash", bg="lightgray")
api_hash_entry = tk.Entry(root, width=40, show="*", font=("Arial", 14))
show_hash_button = tk.Button(root, text="Показать", command=lambda: toggle_token_visibility(api_hash_entry, show_hash_button))

platform_label = tk.Label(root, text="Выберите платформу", bg="lightgray")
platform_label.grid(row=4, column=0, padx=20, pady=5, sticky="w")

platform_var = tk.StringVar(value="ВКонтакте")
platform_combobox = ttk.Combobox(root, textvariable=platform_var, values=["ВКонтакте", "Телеграм"], state="readonly", width=37)
platform_combobox.grid(row=5, column=0, padx=20, pady=5)
platform_combobox.bind("<<ComboboxSelected>>", on_platform_change)

parse_type_label = tk.Label(root, text="Тип парсинга", bg="lightgray")
parse_type_label.grid(row=6, column=0, padx=20, pady=5, sticky="w")

parse_type_var = tk.StringVar(value="Сообщения")
parse_type_combobox = ttk.Combobox(root, textvariable=parse_type_var, values=["Сообщения", "Посты в группах"], state="readonly", width=37)
parse_type_combobox.grid(row=7, column=0, padx=20, pady=5)

id_label = tk.Label(root, text="Введите ID собеседника или ссылку", bg="lightgray")
id_label.grid(row=8, column=0, padx=20, pady=5, sticky="w")

id_entry = tk.Entry(root, width=40)
id_entry.grid(row=9, column=0, padx=20, pady=5)

save_label = tk.Label(root, text="Выберите место, куда сохранить текст", bg="lightgray")
save_label.grid(row=10, column=0, padx=20, pady=5, sticky="w")

path_label = tk.Label(root, text="", bg="lightgray")
path_label.grid(row=11, column=0, padx=20, pady=5, sticky="w")

save_button = tk.Button(root, text="...", command=save_file)
save_button.grid(row=11, column=1, padx=10, pady=5)

# Прогресс-бар
progress_label = tk.Label(root, text="Прогресс:", bg="lightgray")
progress_label.grid(row=12, column=0, padx=20, pady=5, sticky="w")
progress_bar = ttk.Progressbar(root, length=200, mode='determinate')
progress_bar.grid(row=12, column=1, padx=10, pady=5)

# Метка состояния
status_label = tk.Label(root, text="", bg="lightgray", fg="blue")
status_label.grid(row=13, column=0, columnspan=2, padx=20, pady=5)

start_button = tk.Button(root, text="Пуск", width=10, command=start_parsing)
start_button.grid(row=14, column=1, padx=10, pady=20, sticky="e")

root.mainloop()