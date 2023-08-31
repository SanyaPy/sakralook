from datetime import datetime

import telebot
from astropy.coordinates import EarthLocation
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from telebot import types

bot = telebot.TeleBot("6215633342:AAGJuVbMonsMpzN1HO9-69ScXqEIFnv4Ogs")

# Координати України (приблизно центральна частина)
latitude = 50.4501  # широта
longitude = 30.5234  # довгота
elevation = 170  # висота над рівнем моря (у метрах)
location = EarthLocation(lat=latitude, lon=longitude, height=elevation)

ZODIAC_SIGNS_DICT = {
    "Aries": "Овен",
    "Taurus": "Телець",
    "Gemini": "Близнюки",
    "Cancer": "Рак",
    "Leo": "Лев",
    "Virgo": "Діва",
    "Libra": "Терези",
    "Scorpio": "Скорпіон",
    "Sagittarius": "Стрілець",
    "Capricorn": "Козоріг",
    "Aquarius": "Водолій",
    "Pisces": "Риби"
}

# глобальна змінна для завершення реагування на різні типи повідомлень окрім команд
user_statuses = {}


@bot.message_handler(content_types=['sticker', 'photo', 'audio', 'video', 'document', 'location', 'contact', 'voice'])
def handle_non_text(message):
    if not user_statuses.get(message.chat.id):
        bot.reply_to(message, "Будь ласка, надсилайте лише текстові повідомлення.")


# Функція визначення асценденту
def calculate_ascendant_with_flatlib(birth_date, birth_time, timezone):
    lat_deg, lat_min = divmod(abs(latitude) * 60, 60)
    lon_deg, lon_min = divmod(abs(longitude) * 60, 60)

    lat_str = f"{int(lat_deg)}n{int(lat_min):02}" if latitude >= 0 else f"{int(lat_deg)}s{int(lat_min):02}"
    lon_str = f"{int(lon_deg)}e{int(lon_min):02}" if longitude >= 0 else f"{int(lon_deg)}w{int(lon_min):02}"

    date = Datetime(birth_date.strftime('%Y/%m/%d'), birth_time.strftime('%H:%M'), timezone)
    pos = GeoPos(lat_str, lon_str)
    chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)

    ascendant = chart.get(const.ASC)
    ascendant_sign_ukr = ZODIAC_SIGNS_DICT[ascendant.sign]

    return ascendant_sign_ukr


# Перевірка коректності формату часу
def is_valid_time(time_str):
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False


# Функція для перевірки коректності формату дати
def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


# Перевірка коректності значення дня та місяця
def is_valid_day_month(day, month, year=None):
    if not isinstance(day, int) or not isinstance(month, int):
        return False

    if month < 1 or month > 12:
        return False

    if day < 1:
        return False

    if month in [1, 3, 5, 7, 8, 10, 12]:
        return day <= 31
    elif month in [4, 6, 9, 11]:
        return day <= 30
    else:  # February
        return day <= 29 if is_leap_year(year) else day <= 28


# Функція для перевірки високосного року
def is_leap_year(year):
    if year % 4 != 0:
        return False
    elif year % 100 != 0:
        return True
    elif year % 400 != 0:
        return False
    else:
        return True


# /start
@bot.message_handler(commands=['start'])
def start(message):
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    if first_name is None and last_name is None:
        greeting = "Вітаємо!"
    else:
        greeting = f"Вітаємо, {first_name or ''} {last_name or ''}!"

    text = (
        "\nНапишіть, будь ласка, ваші:\n"
        "Дату народження (у форматі РРРР-ММ-ДД): ")

    bot.send_message(message.chat.id, greeting)
    bot.send_message(message.chat.id, text)

    bot.register_next_step_handler(message, process_birth_date)


# Обробник введення дати народження
def process_birth_date(message):
    try:
        if not message.text:
            raise ValueError("Будь ласка, надсилайте лише текстові повідомлення.")
        birth_date_text = message.text.strip()
        if not is_valid_date(birth_date_text):
            raise ValueError("Некоректний формат дати. Будь ласка, введіть у форматі РРРР-ММ-ДД.")

        parts = birth_date_text.split('-')
        if len(parts) != 3 or not is_valid_day_month(int(parts[2]), int(parts[1])):
            raise ValueError("Некоректна дата. Будь ласка, перевірте значення дня та місяця.")

        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        if not is_valid_day_month(day, month):
            raise ValueError("Некоректна дата. Перевірте значення дня та місяця.")

        birth_date = datetime(year, month, day).strftime('%d.%m.%Y')
        bot.send_message(message.chat.id, f"Дані збережено. Ваша дата народження: {birth_date}")
        bot.send_message(message.chat.id, "Введіть час вашого народження (у форматі ГГ:ХХ): ")
        bot.register_next_step_handler(message, process_time_date, birth_date)

    except ValueError as e:
        bot.send_message(message.chat.id, str(e))
        bot.register_next_step_handler(message,
                                       process_birth_date)  # цей рядок знову реєструє обробник наступного кроку


# Обробник введення часу народження
def process_time_date(message, birth_date):
    try:
        if not message.text:
            raise ValueError("Будь ласка, надсилайте лише текстові повідомлення.")
        birth_time = message.text.strip()
        if not is_valid_time(birth_time):
            raise ValueError("Некоректний формат часу. Будь ласка, введіть у форматі ГГ:ХХ.")

        birth_datetime_str = f"{birth_date.split('.')[2]}-{birth_date.split('.')[1]}-{birth_date.split('.')[0]} {birth_time}"
        birth_datetime = datetime.strptime(birth_datetime_str, '%Y-%m-%d %H:%M')
        birth_date_obj = birth_datetime.date()  # Отримання частини дати
        birth_time_obj = birth_datetime.time()  # Отримання частини часу

        timezone = '+03:00'  # Це потрібно буде адаптувати на підставі вашої локації користувача
        ascendant = calculate_ascendant_with_flatlib(birth_date_obj, birth_time_obj, timezone)

        # Відправка повідомлення з асцендентом
        bot.send_message(message.chat.id, f"Дані збережено. Ваш час народження: {birth_time}")
        bot.send_message(message.chat.id, "Ми якнайшвидше повернемось до вас з інформацією про ваш Асцендент 🤍")
        bot.send_message(message.chat.id, f"Ваш асцендент: <b>{ascendant}</b>", parse_mode='HTML')
        bot.send_message(message.chat.id, "Даруємо вам гайд 5 причин ПРОЯВЛЯТИСЬ за Асцендентом 💌")
        bot.send_message(message.chat.id, "Нехай буде в користь💫")

        # Відправлення PDF файлу
        with open("GUIDE_BONUS_5REASONS.pdf", 'rb') as document:
            bot.send_document(message.chat.id, document)
        bot.send_message(message.chat.id, "У разі виникнення будь-яких запитань звертайтесь до @prybulka 🚀")
        user_statuses[message.chat.id] = True



    except ValueError as e:
        bot.send_message(message.chat.id, str(e))
        bot.register_next_step_handler(message,
                                       process_time_date,
                                       birth_date)  # цей рядок знову реєструє обробник наступного кроку


# /website
@bot.message_handler(commands=['website'])
def site(message):
    text = "Ось посилання на сайт: https://www.youtube.com/watch?v=-l_CYgBj4IE"
    bot.send_message(message.chat.id, text)


# /help
@bot.message_handler(commands=['help'])
def help(message):
    text = "Адміністратор Сакралук 🤍"
    keyboard = types.InlineKeyboardMarkup()  # Створюємо клавіатуру з кнопками
    url_button = types.InlineKeyboardButton(text="Написати", url="https://t.me/prybulka")
    keyboard.add(url_button)  # Додаємо кнопку до клавіатури
    bot.send_message(message.chat.id, text, reply_markup=keyboard)  # Відправляємо повідомлення з клавіатурою


bot.polling(none_stop=True)