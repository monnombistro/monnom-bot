import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

from main import search_basket

TOKEN = "8867377662:AAGpuwrAZ-8HzciwYfjTcyqHN-9QYSSQ4qQ"

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🧠 СЛОВАРЬ УМНОГО ПОИСКА (РУССКИЙ/ЛАТИНИЦА/ОПЕЧАТКИ ➔ ПОЛЬСКИЙ ДЛЯ ПОСТАВЩИКОВ)
PRODUCT_DICTIONARY = {
    # Кириллица
    "фавита": "favita",
    "фавтиа": "favita",  # исправление частой опечатки
    "сыр фавита": "favita",
    "лосось": "łosoś",
    "рыба лосось": "łosoś",
    "молоко": "mleko",
    "помидоры": "pomidor",
    "томаты": "pomidor",
    "помидор": "pomidor",
    "картофель": "ziemniaki",
    "картошка": "ziemniaki",
    "сливки": "śmietana",
    "масло сливочное": "masło",
    "мука": "mąka",
    "курица": "kurczak",
    "филе куриное": "kurczak file",
    
    # Латиница (включая ввод без польских символов)
    "maslo": "masło",
    "losos": "łosoś",
    "pomidory": "pomidor",
    "smietana": "śmietana",
    "maka": "mąka",
    "kurczak": "kurczak",
    "favita": "favita",
    "ziemniaki": "ziemniaki",
    "mleko": "mleko"
}

def smart_clean_item(raw_item: str) -> str:
    """Проверяет введенный текст по словарю, исправляет опечатки и переводит."""
    cleaned = raw_item.lower().strip()
    # Если находим точное совпадение или частичное в словаре
    if cleaned in PRODUCT_DICTIONARY:
        return PRODUCT_DICTIONARY[cleaned]
    
    # Если не нашли в словаре, возвращаем как есть (например, если это уникальное название)
    return cleaned

@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "👋 Привет! Я умный бот-закупщик **Monnom Bistro**.\n\n"
        "Отправь мне список продуктов **в столбик** (можно на русском языке или латиницей без польских букв). "
        "Я автоматически переведу их, учту синонимы и опрошу всех поставщиков!\n\n"
        "🛒 *Пример:* \n"
        "favita\n"
        "losos\n"
        "maslo"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message()
async def handle_text_search(message: Message):
    user_text = message.text.strip()
    raw_items = [line.strip() for line in user_text.split("\n") if line.strip()]
    
    if not raw_items:
        await message.answer("⚠️ Пожалуйста, введите хотя бы один товар для поиска.")
        return

    # Прогоняем каждый товар через «умный словарь»
    items = []
    translation_notes = []
    
    for raw in raw_items:
        translated = smart_clean_item(raw)
        items.append(translated)
        if raw.lower() != translated:
            translation_notes.append(f"*{raw}* ➔ `{translated}`")

    # Формируем текст о том, как бот понял запрос
    note_text = ""
    if translation_notes:
        note_text = "\n💡 _Умный поиск применил перевод/синонимы:_\n" + ", ".join(translation_notes) + "\n"

    status_msg = await message.answer(
        f"⏳ Анализирую корзину ({len(items)} поз.)...\n{note_text}", 
        parse_mode="Markdown"
    )

    try:
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(None, search_basket, items)
        
        await message.answer(report, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при обработке корзины: {e}")
    finally:
        try:
            await status_msg.delete()
        except:
            pass

async def main():
    print("🤖 Умный Telegram-бот запущен и ждет сообщения...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())