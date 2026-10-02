import asyncio
import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

from main import search_basket

TOKEN = "8867377662:AAGpuwrAZ-8HzciwYfjTcyqHN-9QYSSQ4qQ"

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🧠 СЛОВАРЬ УМНОГО ПОИСКА
PRODUCT_DICTIONARY = {
    "фавита": "favita", "фавтиа": "favita", "сыр фавита": "favita",
    "лосось": "łosoś", "рыба лосось": "łosoś",
    "молоко": "mleko", "помидоры": "pomidor", "томаты": "pomidor", "помидор": "pomidor",
    "картофель": "ziemniaki", "картошка": "ziemniaki",
    "сливки": "śmietana", "масло сливочное": "masło",
    "мука": "mąka", "курица": "kurczak", "филе куриное": "kurczak file",
    "maslo": "masło", "losos": "łosoś", "pomidory": "pomidor",
    "smietana": "śmietana", "maka": "mąka", "kurczak": "kurczak",
    "favita": "favita", "ziemniaki": "ziemniaki", "mleko": "mleko"
}

def smart_clean_item(raw_item: str) -> str:
    cleaned = raw_item.lower().strip()
    return PRODUCT_DICTIONARY.get(cleaned, cleaned)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "👋 Привет! Я умный бот-закупщик **Monnom Bistro**.\n\n"
        "Отправь мне список продуктов **в столбик** (на русском или латиницей без польских букв). "
        "Я всё переведу и найду самые выгодные цены!\n\n"
        "🛒 *Пример:* \nfavita\nlosos\nmaslo"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message()
async def handle_text_search(message: Message):
    user_text = message.text.strip()
    raw_items = [line.strip() for line in user_text.split("\n") if line.strip()]
    
    if not raw_items:
        await message.answer("⚠️ Пожалуйста, введите хотя бы один товар.")
        return

    items, translation_notes = [], []
    for raw in raw_items:
        translated = smart_clean_item(raw)
        items.append(translated)
        if raw.lower() != translated:
            translation_notes.append(f"*{raw}* ➔ `{translated}`")

    note_text = "\n💡 _Умный поиск применил перевод:_\n" + ", ".join(translation_notes) + "\n" if translation_notes else ""
    status_msg = await message.answer(f"⏳ Анализирую корзину ({len(items)} поз.)...\n{note_text}", parse_mode="Markdown")

    try:
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(None, search_basket, items)
        await message.answer(report, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        try:
            await status_msg.delete()
        except:
            pass

# --- ФЕЙКОВЫЙ ВЕБ-СЕРВЕР ДЛЯ ОБЛАКА ---
async def health_check(request):
    return web.Response(text="Bot is running and healthy!")

async def main():
    print("🤖 Бот запущен! Инициализация...")
    
    # Запускаем микро-сервер на порту, который выдаст Render
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"🌐 Облачный порт {port} открыт. Запускаю поллинг Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())