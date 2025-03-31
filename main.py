import logging
import os
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API keys from environment variables
API_KEY = os.getenv("OPENWEATHER_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Check if API keys are missing
if not API_KEY:
    logger.error("❌ OPENWEATHER_API_KEY is missing! Set it in Railway.")
if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN is missing! Set it in Railway.")

# Store user session data
temp_data = {}

async def get_weather(city: str):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        logger.info(f"Fetching weather data for: {city}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    return None
                
                data = await response.json()
                logger.info(f"API Response: {data}")

        if "main" not in data or "weather" not in data:
            logger.error(f"Invalid API response: {data}")
            return None

        weather_info = {
            "temperature": data["main"].get("temp", "N/A"),
            "humidity": data["main"].get("humidity", "N/A"),
            "wind_speed": data["wind"].get("speed", "N/A"),
            "condition": data["weather"][0].get("description", "N/A").capitalize(),
        }
        return weather_info
    except Exception as e:
        logger.error(f"❌ Error fetching weather: {e}")
        return None

async def start(update: Update, context: CallbackContext):
    logger.info("/start command received.")
    await update.message.reply_text("Hey there! 😊 I'm CareCast, your friendly weather assistant. Hope you're having a great day! Just ask me about the weather in any city 🌍")

async def weather(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    message_text = update.message.text.lower()

    words = message_text.split()
    city = None

    if "weather" in words:
        prepositions = ["in", "for", "at", "of", "near", "around"]
        for prep in prepositions:
            if prep in words:
                city_index = words.index(prep) + 1
                if city_index < len(words):
                    city = " ".join(words[city_index:]).title()
                    break

    logger.info(f"Extracted city: {city}")

    if city:
        temp_data[user_id] = city
        weather_info = await get_weather(city)
        if weather_info:
            response = (
                f"☀️ Hey there! Here's the latest weather update for {city}:
"
                f"🌡 Temperature: {weather_info['temperature']}°C\n"
                f"💧 Humidity: {weather_info['humidity']}%\n"
                f"🌬 Wind Speed: {weather_info['wind_speed']} km/h\n"
                f"☁️ Condition: {weather_info['condition']}\n\n"
                "Take care, stay hydrated, and have an amazing day ahead! 💙"
            )
            await update.message.reply_text(response)
            await update.message.reply_text(f"Hey, want to hear a cool fact about {city}? 😊 Just say 'Yes' or 'No'!")
        else:
            await update.message.reply_text(f"Oh no! 😕 I couldn't fetch the weather for {city}. Maybe try another city? I'm here to help! 💙")
    else:
        await update.message.reply_text("Oops! I couldn't catch the city name. Try something like: 'What's the weather like in Mumbai?' 😊")

async def fun_fact_response(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    city = temp_data.get(user_id, "this city")
    await update.message.reply_text(f"Here's a fun fact about {city}! 🌍 Did you know...? (Feature coming soon) 💙")

async def no_fun_fact(update: Update, context: CallbackContext):
    await update.message.reply_text("No worries! If you ever need a weather update, just ask! Stay awesome! ☀️💙")

async def unknown(update: Update, context: CallbackContext):
    logger.info(f"Unknown command received: {update.message.text}")
    await update.message.reply_text("Hmm... I didn't quite get that! But I'm here for weather updates—just ask! 🌍☀️")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Regex(r"(?i)^(.*weather.*(in|for|at|of|near|around) .+|what's the weather.*|today's weather.*|how's the weather.*|tell me the weather.*|give me the weather.*)$"), weather))
app.add_handler(MessageHandler(filters.Regex(r"(?i)^Yes$"), fun_fact_response))
app.add_handler(MessageHandler(filters.Regex(r"(?i)^No$"), no_fun_fact))
app.add_handler(MessageHandler(filters.ALL, unknown))

logger.info("🚀 Bot is running...")
app.run_polling()

