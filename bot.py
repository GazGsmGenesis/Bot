import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    KeyboardBuilder,
    KeyboardButton
)

# Твой токен бота, который ты прислал
TOKEN = "9024589074:AAGOR8B30oFJCSkQp1Wfh8xAlakaAHEB_d0"

# Юзернейм твоего менеджера (замени на свой, если нужно)
MANAGER_USERNAME = "telsupport"  

# Путь к файлу программы, который будет отправляться по кнопке Download
PROGRAM_FILE_PATH = "program.zip"  

router = Router()

# Состояния для пошагового сценария с ключами
class KeyOrderStates(StatesGroup):
    waiting_for_model = State()
    waiting_for_confirmation = State()

# Список моделей iPhone для вывода
IPHONE_MODELS_TEXT = (
    "📱 Выбери нужную модель устройства (отправь цифру):\n\n"
    "1. iPhone 10\n"
    "2. iPhone 11\n"
    "3. iPhone 12\n"
    "4. iPhone 13\n"
    "5. iPhone 14\n"
    "6. iPhone 15\n"
    "7. iPhone 16"
)

# Словарь для сопоставления цифр с названиями моделей
MODELS_MAP = {
    "1": "iPhone 10",
    "2": "iPhone 11",
    "3": "iPhone 12",
    "4": "iPhone 13",
    "5": "iPhone 14",
    "6": "iPhone 15",
    "7": "iPhone 16",
}

# Главное меню с двумя кнопками
def get_main_keyboard():
    builder = KeyboardBuilder(button_type=KeyboardButton)
    builder.add(KeyboardButton(text=" Key"))
    builder.add(KeyboardButton(text=" Download"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Кнопки подтверждения [y/n]
def get_yn_keyboard():
    builder = KeyboardBuilder(button_type=KeyboardButton)
    builder.add(KeyboardButton(text="y"), KeyboardButton(text="n"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Выбери нужное действие в меню ниже:",
        reply_markup=get_main_keyboard()
    )

# Обработка нажатия на кнопку "🔑 Key"
@router.message(F.text == "Key")
async def process_key_button(message: Message, state: FSMContext):
    await state.set_state(KeyOrderStates.waiting_for_model)
    await message.answer(IPHONE_MODELS_TEXT)

# Обработка ввода цифры модели
@router.message(KeyOrderStates.waiting_for_model)
async def process_model_choice(message: Message, state: FSMContext):
    choice = message.text.strip()
    if choice not in MODELS_MAP:
        await message.answer(" Неверный выбор. Пожалуйста, отправь цифру от 1 до 7:")
        return
    
    selected_model = MODELS_MAP[choice]
    await state.update_data(selected_model=selected_model)
    
    await state.set_state(KeyOrderStates.waiting_for_confirmation)
    await message.answer(
        f"Ты выбрал: **{selected_model}**.\nПодтверждаешь выбор? [y/n]",
        parse_mode="Markdown",
        reply_markup=get_yn_keyboard()
    )

# Обработка ответа [y/n]
@router.message(KeyOrderStates.waiting_for_confirmation)
async def process_confirmation(message: Message, state: FSMContext):
    answer = message.text.strip().lower()
    
    if answer == "y":
        data = await state.get_data()
        model = data.get("selected_model")
        
        # Создаем инлайн-кнопку с переходом на менеджера
        manager_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=" Написать менеджеру", url=f"https://t.me/de_zhomur")]
            ]
        )
        
        await message.answer(
            f" Запрос по модели **{model}** принят!\n\n"
            f"Для оплаты и получения ключа свяжитесь с нашим менеджером:",
            parse_mode="Markdown",
            reply_markup=manager_kb
        )
        await state.clear()
        await message.answer("Главное меню:", reply_markup=get_main_keyboard())
        
    elif answer == "n":
        await message.answer(" Действие отменено.", reply_markup=get_main_keyboard())
        await state.clear()
    else:
        await message.answer("Пожалуйста, отправь только букву **y** (да) или **n** (нет):", parse_mode="Markdown")

# Обработка нажатия на кнопку "📥 Download"
@router.message(F.text == " Download")
async def process_download_button(message: Message):
    await message.answer("⏳ Загружаю файл программы, подожди пару секунд...")
    try:
        file = FSInputFile(PROGRAM_FILE_PATH)
        await message.answer_document(file, caption="")
    except Exception as e:
        await message.answer(" Ошибка: файл программы не найден.")

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот успешно запущен и работает!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
