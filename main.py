import logging
import os
import requests
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

def get_weather(city: str):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        logger.info(f"Fetching weather data for: {city}")

        response = requests.get(url)
        response.raise_for_status()  # Raises an error if response is not 200
        data = response.json()

        # Ensure API response is valid
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
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching weather: {e}")
        return None

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello! 😊 I'm CareCast, your weather assistant. Just ask me about the weather in any city 🌍")

async def weather(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    message_text = update.message.text.lower()  # Convert entire message to lowercase

    # Extract city name (everything after "weather in")
    words = message_text.split()
    city = None

    if "weather" in words and "in" in words:
        city_index = words.index("in") + 1
        if city_index < len(words):  # Ensure there's a city name after "in"
            city = " ".join(words[city_index:]).title()  # Convert to title case for better readability

    logger.info(f"Extracted city: {city}")  # Debugging log

    if city:
        temp_data[user_id] = city  # Store city for follow-ups
        weather_info = get_weather(city)
        if weather_info:
            response = (
                f"🌍 Weather update for {city}:\n"
                f"🌡 Temperature: {weather_info['temperature']}°C\n"
                f"💧 Humidity: {weather_info['humidity']}%\n"
                f"🌬 Wind Speed: {weather_info['wind_speed']} km/h\n"
                f"☁️ Condition: {weather_info['condition']}\n\n"
                "Stay safe and take care! 💙"
            )
            await update.message.reply_text(response)
            await update.message.reply_text(f"Would you like to hear a fun fact about {city}? 😊 (Yes/No)")
        else:
            await update.message.reply_text(f"Oops! 😕 I couldn't fetch the weather for {city}. Try another city or check your spelling. I'm here to help! 💙")
    else:
        await update.message.reply_text("I couldn't detect the city name. Try: 'What's the weather in Chennai?' 😊")

async def fun_fact_response(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    city = temp_data.get(user_id, "this city")
    await update.message.reply_text(f"Here's a fun fact about {city}! 🌍 Did you know...? (Feature coming soon) 💙")

async def no_fun_fact(update: Update, context: CallbackContext):
    await update.message.reply_text("Got it! If you need more weather updates, just ask. Stay safe! ☀️💙")

async def unknown(update: Update, context: CallbackContext):
    await update.message.reply_text("I'm not sure I understood. I can provide today's weather updates—just ask! 🌍☀️")

# Build Telegram bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Regex(r"(?i)^(weather in .+|what's the weather in .+|today's weather in .+)"), weather))
app.add_handler(MessageHandler(filters.Regex(r"(?i)^Yes$"), fun_fact_response))
app.add_handler(MessageHandler(filters.Regex(r"(?i)^No$"), no_fun_fact))
app.add_handler(MessageHandler(filters.ALL, unknown))

logger.info("🚀 Bot is running...")
app.run_polling()
