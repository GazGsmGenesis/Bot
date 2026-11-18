import os
import time
import requests

TOKEN = "9024589074:AAGOR8B30oFJCSkQp1Wfh8xAlakaAHEB_d0"
MANAGER_USERNAME = "de_zhomur"
PROGRAM_FILE_PATH = "program.zip"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

user_states = {}

def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def send_document(chat_id, file_path, caption):
    url = f"{BASE_URL}/sendDocument"
    if not os.path.exists(file_path):
        send_message(chat_id, "Ошибка: файл не найден.")
        return
    with open(file_path, "rb") as f:
        files = {"document": f}
        data = {"chat_id": chat_id, "caption": caption}
        requests.post(url, data=data, files=files)

def get_main_keyboard():
    return {
        "keyboard": [
            [{"text": "Key"}, {"text": "Download"}]
        ],
        "resize_keyboard": True
    }

def get_yn_keyboard():
    return {
        "keyboard": [
            [{"text": "y"}, {"text": "n"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }

MODELS_TEXT = (
    "Выбери модель (отправь цифру):\n\n"
    "1. iPhone 10\n"
    "2. iPhone 11\n"
    "3. iPhone 12\n"
    "4. iPhone 13\n"
    "5. iPhone 14\n"
    "6. iPhone 15\n"
    "7. iPhone 16"
)

MODELS_MAP = {
    "1": "iPhone 10",
    "2": "iPhone 11",
    "3": "iPhone 12",
    "4": "iPhone 13",
    "5": "iPhone 14",
    "6": "iPhone 15",
    "7": "iPhone 16",
}

def handle_update(update):
    message = update.get("message")
    if not message:
        return
    
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    
    state = user_states.get(chat_id, {})
    current_step = state.get("step")
    
    if text == "/start":
        user_states[chat_id] = {}
        send_message(chat_id, "Главное меню:", reply_markup=get_main_keyboard())
        return

    if text == "Key":
        user_states[chat_id] = {"step": "waiting_for_model"}
        send_message(chat_id, MODELS_TEXT)
        return

    if text == "Download":
        send_message(chat_id, "Загрузка...")
        send_document(chat_id, PROGRAM_FILE_PATH, "Файл программы:")
        return

    if current_step == "waiting_for_model":
        if text not in MODELS_MAP:
            send_message(chat_id, "Неверно. Отправь цифру от 1 до 7:")
            return
        
        selected_model = MODELS_MAP[text]
        user_states[chat_id] = {"step": "waiting_for_confirmation", "model": selected_model}
        
        send_message(
            chat_id,
            f"Выбрано: *{selected_model}*. Подтверждаешь? [y/n]",
            reply_markup=get_yn_keyboard()
        )
        return

    if current_step == "waiting_for_confirmation":
        answer = text.lower()
        if answer == "y":
            model = state.get("model")
            manager_kb = {
                "inline_keyboard": [
                    [{"text": "Написать менеджеру", "url": f"https://t.me/{MANAGER_USERNAME}"}]
                ]
            }
            send_message(
                chat_id,
                f"Запрос по *{model}* принят. Напиши менеджеру для получения:",
                reply_markup=manager_kb
            )
            user_states[chat_id] = {}
            send_message(chat_id, "Главное меню:", reply_markup=get_main_keyboard())
            
        elif answer == "n":
            user_states[chat_id] = {}
            send_message(chat_id, "Отменено.", reply_markup=get_main_keyboard())
        else:
            send_message(chat_id, "Отправь только *y* или *n*:")
        return

def main():
    print("Бот запущен!")
    offset = 0
    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if data.get("ok"):
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    handle_update(update)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
