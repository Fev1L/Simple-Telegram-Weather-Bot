from pyexpat.errors import messages

import telebot
from telebot import types
import requests
import json

from telebot.types import InlineKeyboardButton

bot = telebot.TeleBot('XXX')
API = 'XXX'
user_lang = {}
last_city = {}
last_queries = []

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_lang_code = message.from_user.language_code

    if user_lang_code.startswith('uk'):
        user_lang[chat_id] = 'uk'
    else:
        user_lang[chat_id] = 'en'

    lang = user_lang[chat_id]
    text = "Welcome! Please enter your city:" if lang == 'en' else "Ласкаво просимо! Введіть ваше місто:"
    bot.send_message(chat_id, text)

@bot.message_handler(content_types=['text'])
def weather_city(message):
    city = message.text.strip().lower()
    last_city[message.chat.id] = message
    lang = user_lang[message.chat.id]

    if city not in last_queries:
        last_queries.insert(0, city)
    if len(last_queries) > 3:
        last_queries.pop()

    markup = types.ReplyKeyboardMarkup()
    for q in last_queries:
        markup.row(q)

    inline_markup = types.InlineKeyboardMarkup()
    if lang == 'en':
        inline_markup.add(InlineKeyboardButton("🔄 Repeat", callback_data="repeat"))
    elif lang == 'uk':
        inline_markup.add(InlineKeyboardButton("🔄 Повторити", callback_data="repeat"))

    geo = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={city},&limit={1}&appid={API}")
    if geo.status_code == 200:
        data = json.loads(geo.text)
        lat = data[0]['lat']
        lon = data[0]['lon']
    else:
        if lang == 'en':
            bot.reply_to(message, 'Something went wrong')
        elif lang == 'uk':
            bot.reply_to(message, 'Щось пішло не так')

    res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API}&units=metric')
    if res.status_code == 200:
        data = json.loads(res.text)
        weather_main = data['weather'][0]['main']
        if weather_main == "Clear":
            weather_emoji = "☀️"
        elif weather_main == "Clouds":
            weather_emoji = "☁️"
        elif weather_main == "Rain":
            weather_emoji = "🌧"
        elif weather_main == "Snow":
            weather_emoji = "❄️"
        elif weather_main == "Thunderstorm":
            weather_emoji = "⛈"
        elif weather_main == "Drizzle":
            weather_emoji = "🌦"
        elif weather_main in ["Mist", "Fog", "Haze"]:
            weather_emoji = "🌫"
        else:
            weather_emoji = "🌍"

        clouds = data['clouds']['all']
        if clouds < 20:
            cloud_emoji = "☀️"
        elif clouds < 50:
            cloud_emoji = "🌤"
        elif clouds < 80:
            cloud_emoji = "⛅"
        else:
            cloud_emoji = "☁️"

        wind_speed = data['wind']['speed']
        if wind_speed < 3:
            wind_emoji = "🍃"
        elif wind_speed < 8:
            wind_emoji = "🌬"
        else:
            wind_emoji = "💨"

        deg = data['wind']['deg']
        deg = deg % 360

        if 22.5 <= deg < 67.5:
            deg_emoji = "↗"
        elif 67.5 <= deg < 112.5:
            deg_emoji = "→"
        elif 112.5 <= deg < 157.5:
            deg_emoji = "↘"
        elif 157.5 <= deg < 202.5:
            deg_emoji = "↓"
        elif 202.5 <= deg < 247.5:
            deg_emoji = "↙"
        elif 247.5 <= deg < 292.5:
            deg_emoji = "←"
        elif 292.5 <= deg < 337.5:
            deg_emoji = "↖"
        else:
            deg_emoji = "↑"

        temp = data['main']['temp']
        wind_gust = data['wind'].get('gust', None)
        if lang == 'en':
            bot.reply_to(message,
            f'''
    Weather in {data['name']} now: 
        Weather: {data['weather'][0]['main']} {weather_emoji}
        Temperature: {temp} C 🌡
        Feels like: {data['main']['feels_like']} C 🌡
        Atmospheric pressure: {data['main']['pressure']} hPa 🫠
        Humidity: {data["main"]["humidity"]} % 💧
        Visibility: {data['visibility']} km 👀
        Wind speed: {data['wind']['speed']} m/s {wind_emoji}
        Wind direction: {data['wind']['deg']}  {deg_emoji}
        Wind gust: {wind_gust if wind_gust else 'N/A'} m/s 🌬
        Clouds: {data['clouds']['all']} % {cloud_emoji}
                         ''',reply_markup=inline_markup)
            bot.send_message(message.chat.id, "Chose next city:", reply_markup=markup)
        elif lang == 'uk':
            bot.reply_to(message,
                         f'''
    Погода в {data['name']} зараз: 
        Погода: {weather_emoji}
        Температра: {temp} C 🌡
        Відчувається як: {data['main']['feels_like']} C 🌡
        Атмосферний тиск: {data['main']['pressure']} hPa 🫠
        Вологість: {data["main"]["humidity"]} % 💧
        Видимість: {data['visibility']} km 👀
        Швидкість вітру: {data['wind']['speed']} м/с {wind_emoji}
        Напрямок вітру: {data['wind']['deg']}  {deg_emoji}
        Пориви вітру: {wind_gust if wind_gust else 'Н/Д'} м/с 🌬
        Хмарність: {data['clouds']['all']} % {cloud_emoji}
                                     ''', reply_markup=inline_markup)
            bot.send_message(message.chat.id, "Виберіть наступне місто:", reply_markup=markup)
    else:
        if lang == 'en':
            bot.reply_to(message, 'Something went wrong')
        elif lang == 'uk':
            bot.reply_to(message, 'Щось пішло не так')


@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    city = last_city.get(call.message.chat.id, None)
    lang = user_lang[call.message.chat.id]
    if call.data == "repeat":
        if lang == 'en':
            bot.answer_callback_query(call.id, "Updating...")
        elif lang == 'uk':
            bot.answer_callback_query(call.id, "Обновлюю...")
        weather_city(city)

bot.polling(none_stop=True)