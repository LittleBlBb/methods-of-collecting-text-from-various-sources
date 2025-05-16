import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
import os
import asyncio
import threading
from parse_messages_from_vkontakte import VkApiHandler
from parse_messages_from_telegram import TelegramApiHandler

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
        root.update()

def toggle_token_visibility(entry, button):
    if entry.cget("show") == "*":
        entry.config(show="")
        button.config(text="🙈")
    else:
        entry.config(show="*")
        button.config(text="👁")

def update_progress(current, total):
    if progress_bar:
        progress_bar['value'] = (current / total) * 100
        root.after(0, root.update_idletasks)

def set_ui_state(enabled):
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
    if status_label:
        status_label.config(text=text)
        root.after(0, root.update_idletasks)

async def parse_from_vk_async():
    global save_folder, progress_bar, is_parsing
    if not save_folder:
        root.after(0, lambda: messagebox.showerror("Ошибка", "Выберите папку для сохранения!"))
        return

    username = id_entry.get()
    access_token = token_entry.get()
    if not username or not access_token:
        root.after(0, lambda: messagebox.showerror("Ошибка", "Введите имя пользователя и токен!"))
        return

    # Create an instance of VkApiHandler
    vk_handler = VkApiHandler()
    result = await vk_handler.get_user_id(username, access_token)
    if isinstance(result, tuple):
        user_id, error = result
        if error:
            root.after(0, lambda: messagebox.showerror("Ошибка", error))
            return
    else:
        user_id = result

    if not user_id:
        root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось получить ID пользователя!"))
        return

    is_parsing = True
    set_ui_state(False)
    update_status("Идёт парсинг...")
    progress_bar['value'] = 0

    parse_type = parse_type_var.get()
    try:
        if parse_type == "Сообщения":
            data, error = await vk_handler.get_full_conversation(user_id, access_token, update_progress)
            if error:
                root.after(0, lambda: messagebox.showerror("Ошибка", error))
                return
            filename = f"conversation_vk_{username}.json"
        elif parse_type == "Последние посты":
            data = await vk_handler.get_user_posts_in_groups_limited(user_id, access_token, update_progress=update_progress)
            filename = f"vk_user_posts_limited_{username}.json"
        else:
            data = await vk_handler.get_user_posts_in_groups_full(user_id, access_token, update_progress=update_progress)
            filename = f"vk_user_posts_full_{username}.json"

        save_path = os.path.join(save_folder, filename)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Данные ВКонтакте сохранены в {save_path}")
        root.after(0, lambda: messagebox.showinfo("Успех", f"Данные сохранены в {save_path}"))
    except Exception as e:
        error_msg = str(e)
        print(f"Ошибка парсинга ВКонтакте: {error_msg}")
        root.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось получить данные: {error_msg}"))
    finally:
        root.after(0, lambda: progress_bar.__setitem__('value', 100))
        root.after(0, lambda: set_ui_state(True))
        root.after(0, lambda: update_status(""))
        is_parsing = False

async def parse_from_telegram_async():
    global save_folder, progress_bar, is_parsing
    if not save_folder:
        root.after(0, lambda: messagebox.showerror("Ошибка", "Выберите папку для сохранения!"))
        return

    chat_name = id_entry.get()
    api_id = token_entry.get()
    api_hash = api_hash_entry.get()
    if not all([chat_name, api_id, api_hash]):
        root.after(0, lambda: messagebox.showerror("Ошибка", "Заполните все поля!"))
        return
    tg_handler = TelegramApiHandler()
    is_parsing = True
    set_ui_state(False)
    update_status("Идёт парсинг...")
    progress_bar['value'] = 0

    try:
        client = await tg_handler.telegram_connect(api_id, api_hash, root)
        if not client:
            root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось подключиться к Telegram"))
            return

        async with client:
            chat_history, error = await tg_handler.fetch_chat_history(client, chat_name, update_progress)
            if error:
                root.after(0, lambda: messagebox.showerror("Ошибка", error))
                return

        save_path = os.path.join(save_folder, f"conversation_telegram_{chat_name}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=4)
        print(f"Данные Telegram сохранены в {save_path}")
        root.after(0, lambda: messagebox.showinfo("Успех", f"Данные сохранены в {save_path}"))
    except Exception as e:
        error_msg = str(e)
        print(f"Ошибка парсинга Telegram: {error_msg}")
        root.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось получить данные: {error_msg}"))
    finally:
        root.after(0, lambda: progress_bar.__setitem__('value', 100))
        root.after(0, lambda: set_ui_state(True))
        root.after(0, lambda: update_status(""))
        is_parsing = False

def parse_from_vk():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(parse_from_vk_async())
    finally:
        loop.close()

def parse_from_telegram():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(parse_from_telegram_async())
    finally:
        loop.close()

def run_in_thread(func):
    def wrapper():
        global is_parsing
        if is_parsing:
            messagebox.showwarning("Предупреждение", "Дождитесь завершения текущей операции!")
            return
        thread = threading.Thread(target=func, daemon=True)
        thread.start()
    return wrapper

def start_parsing():
    platform = platform_var.get()
    if platform == "ВКонтакте":
        run_in_thread(parse_from_vk)()
    else:
        run_in_thread(parse_from_telegram)()

def on_platform_change(event):
    platform = platform_var.get()
    if platform == "Телеграм":
        api_hash_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        api_hash_entry.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        show_hash_button.grid(row=5, column=1, padx=5, pady=5)
        token_label.config(text="Введите API ID")
        parse_type_label.grid_remove()
        parse_type_combobox.grid_remove()
    else:
        api_hash_label.grid_remove()
        api_hash_entry.grid_remove()
        show_hash_button.grid_remove()
        token_label.config(text="Введите API токен")
        parse_type_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        parse_type_combobox.grid(row=5, column=0, padx=10, pady=5, sticky="w")

# Создаем основное окно
root = tk.Tk()
root.title("Data Parser")
root.geometry("800x700")

# Стили
style = ttk.Style()
style.theme_use('clam')
style.configure("TCombobox", fieldbackground="#2d3436", background="#2d3436", foreground="white", arrowcolor="#dfe6e9", borderwidth=0, padding=5)
style.configure("TProgressbar", background="#00b894", troughcolor="#2d3436", thickness=12, borderwidth=0)
style.map("TCombobox", fieldbackground=[('readonly', '#2d3436')], selectbackground=[('readonly', '#2d3436')])

# Контейнер с закругленным эффектом
main_frame = tk.Frame(root, bg="#1e272e", padx=20, pady=20)
main_frame.pack(fill="both", expand=True, padx=15, pady=15)

# Полотно для закругленного фона
content_canvas = tk.Canvas(main_frame, bg="#1e272e", highlightthickness=0)
content_canvas.pack(fill="both", expand=True)
content_canvas.create_oval(10, 10, 780, 680, fill="#2d3436", outline="#2d3436")

content_frame = tk.Frame(content_canvas, bg="#2d3436")
content_frame.place(relx=0.5, rely=0.5, anchor="center", width=760, height=660)

# Заголовок
title_label = tk.Label(content_frame, text="Парсер Социальных Сетей", font=("Helvetica", 24, "bold"), bg="#2d3436", fg="#dfe6e9")
title_label.pack(pady=20)

# Поля ввода
input_frame = tk.Frame(content_frame, bg="#2d3436")
input_frame.pack(fill="x", padx=20)

token_label = tk.Label(input_frame, text="Введите API токен", font=("Arial", 12), bg="#2d3436", fg="#dfe6e9")
token_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

token_entry = tk.Entry(input_frame, width=35, show="*", font=("Arial", 12), bg="#1e272e", fg="white", insertbackground="white", relief="flat", borderwidth=2)
token_entry.grid(row=1, column=0, padx=10, pady=5, sticky="w")

show_token_button = tk.Button(input_frame, text="👁", font=("Arial", 12), bg="#0984e3", fg="white", activebackground="#0652dd", relief="flat", borderwidth=0, width=3, command=lambda: toggle_token_visibility(token_entry, show_token_button))
show_token_button.grid(row=1, column=1, padx=5, pady=5)

api_hash_label = tk.Label(input_frame, text="Введите API hash", font=("Arial", 12), bg="#2d3436", fg="#dfe6e9")
api_hash_entry = tk.Entry(input_frame, width=35, show="*", font=("Arial", 12), bg="#1e272e", fg="white", insertbackground="white", relief="flat", borderwidth=2)
show_hash_button = tk.Button(input_frame, text="👁", font=("Arial", 12), bg="#0984e3", fg="white", activebackground="#0652dd", relief="flat", borderwidth=0, width=3, command=lambda: toggle_token_visibility(api_hash_entry, show_hash_button))

platform_label = tk.Label(input_frame, text="Выберите платформу", font=("Arial", 12), bg="#2d3436", fg="#dfe6e9")
platform_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

platform_var = tk.StringVar(value="ВКонтакте")
platform_combobox = ttk.Combobox(input_frame, textvariable=platform_var, values=["ВКонтакте", "Телеграм"], state="readonly", width=33, font=("Arial", 12))
platform_combobox.grid(row=3, column=0, padx=10, pady=5, sticky="w")
platform_combobox.bind("<<ComboboxSelected>>", on_platform_change)

parse_type_label = tk.Label(input_frame, text="Тип парсинга", font=("Arial", 12), bg="#2d3436", fg="#dfe6e9")
parse_type_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")

parse_type_var = tk.StringVar(value="Сообщения")
parse_type_combobox = ttk.Combobox(input_frame, textvariable=parse_type_var, values=["Сообщения", "Последние посты", "Все посты"], state="readonly", width=33, font=("Arial", 12))
parse_type_combobox.grid(row=5, column=0, padx=10, pady=5, sticky="w")

id_label = tk.Label(input_frame, text="Введите ID или ссылку", font=("Arial", 12), bg="#2d3436", fg="#dfe6e9")
id_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")

id_entry = tk.Entry(input_frame, width=35, font=("Arial", 12), bg="#1e272e", fg="white", insertbackground="white", relief="flat", borderwidth=2)
id_entry.grid(row=7, column=0, padx=10, pady=5, sticky="w")

save_label = tk.Label(input_frame, text="Выберите папку для сохранения", font=("Arial", 12), bg="#2d3436", fg="#dfe6e9")
save_label.grid(row=8, column=0, padx=10, pady=5, sticky="w")

path_label = tk.Label(input_frame, text="", font=("Arial", 12), bg="#2d3436", fg="#00b894")
path_label.grid(row=9, column=0, columnspan=2, padx=10, pady=5, sticky="w")

save_button = tk.Button(input_frame, text="📁", font=("Arial", 12), bg="#fdcb6e", fg="#2d3436", activebackground="#e7b558", relief="flat", borderwidth=0, width=3, command=save_file)
save_button.grid(row=9, column=2, padx=5, pady=5)

# Прогресс-бар и статус
progress_frame = tk.Frame(content_frame, bg="#2d3436")
progress_frame.pack(fill="x", padx=20, pady=10)

progress_label = tk.Label(progress_frame, text="Прогресс:", font=("Arial", 12), bg="#2d3436", fg="#dfe6e9")
progress_label.pack(anchor="w")

progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
progress_bar.pack(fill="x", pady=5)

status_label = tk.Label(progress_frame, text="", font=("Arial", 12, "italic"), bg="#2d3436", fg="#00b894")
status_label.pack(anchor="w", pady=5)

# Круглая кнопка пуска
start_frame = tk.Frame(content_frame, bg="#2d3436")
start_frame.pack(pady=10)
start_canvas = tk.Canvas(start_frame, bg="#2d3436", highlightthickness=0, width=120, height=120)
start_canvas.pack()
start_button = tk.Button(start_canvas, text="Пуск", font=("Arial", 16, "bold"), bg="#e84393", fg="white", activebackground="#c23675", relief="flat", borderwidth=0, width=5, height=1, command=start_parsing)
start_canvas.create_window(60, 60, window=start_button)

# Эффекты наведения для кнопок
for btn in [show_token_button, show_hash_button, save_button, start_button]:
    btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=b.cget("activebackground")))
    btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=b.cget("background")))

root.mainloop()