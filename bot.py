import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

TOKEN = "9024589074:AAH5tc2vYZi01dpFDEgUm37oLFHJoSfcUAI"
MANAGER_USERNAME = "de_zhomur"
PROGRAM_FILE_PATH = "program.zip"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

user_states = {}
processed_updates = set()

# Мини-сервер для Render
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def send_document(chat_id, file_path, caption):
    url = f"{BASE_URL}/sendDocument"
    if not os.path.exists(file_path):
        send_message(chat_id, "Error: file not found.")
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
    "Choose a model (send a digit):\n\n"
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
    update_id = update.get("update_id")
    
    # Защита от дублирования одного и того же события
    if update_id in processed_updates:
        return
    processed_updates.add(update_id)
    if len(processed_updates) > 100:
        processed_updates.pop()

    message = update.get("message")
    if not message:
        return
    
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    
    state = user_states.get(chat_id, {})
    current_step = state.get("step")
    
    if text == "/start":
        user_states[chat_id] = {}
        send_message(chat_id, "Main menu:", reply_markup=get_main_keyboard())
        return

    if text == "Key":
        user_states[chat_id] = {"step": "waiting_for_model"}
        send_message(chat_id, MODELS_TEXT)
        return

    if text == "Download":
        send_message(chat_id, "Downloading...")
        send_document(chat_id, PROGRAM_FILE_PATH, "Your program file:")
        return

    if current_step == "waiting_for_model":
        if text not in MODELS_MAP:
            send_message(chat_id, "Invalid choice. Send a digit from 1 to 7:")
            return
        
        selected_model = MODELS_MAP[text]
        user_states[chat_id] = {"step": "waiting_for_confirmation", "model": selected_model}
        
        send_message(
            chat_id,
            f"Selected: *{selected_model}*. Confirm? [y/n]",
            reply_markup=get_yn_keyboard()
        )
        return

    if current_step == "waiting_for_confirmation":
        answer = text.lower()
        if answer == "y":
            model = state.get("model")
            manager_kb = {
                "inline_keyboard": [
                    [{"text": "Contact Manager", "url": f"https://t.me/{MANAGER_USERNAME}"}]
                ]
            }
            send_message(
                chat_id,
                f"Request for *{model}* accepted. Contact the manager to get it:",
                reply_markup=manager_kb
            )
            user_states[chat_id] = {}
            send_message(chat_id, "Main menu:", reply_markup=get_main_keyboard())
            
        elif answer == "n":
            user_states[chat_id] = {}
            send_message(chat_id, "Cancelled.", reply_markup=get_main_keyboard())
        else:
            send_message(chat_id, "Please send only *y* or *n*:")
        return

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    print("Bot started successfully!")
    
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
            print(f"Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
