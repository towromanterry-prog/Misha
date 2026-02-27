# config.py
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (если он существует)
load_dotenv()

# --- НАСТРОЙКИ ИНТЕРФЕЙСА ---
THEME_MODE = "light"      # "light", "dark", "system"
THEME_COLOR = "blue"      # "blue", "green", "dark-blue"
APP_TITLE = "AURORA.GERMES"


# --- НОВЫЕ ПАРАМЕТРЫ ДЛЯ ПОЧТЫ (SMTP) ---
SMTP_SERVER = "smtp.yandex.ru"          # Замените на ваш SMTP сервер (например, smtp.mail.ru или корпоративный)
SMTP_PORT = 465                         # Обычно 465 для SSL или 587 для TLS
SMTP_LOGIN = "your_email@domain.ru"     # Почта, с которой будет идти отправка
SMTP_PASSWORD = "your_app_password"     # Пароль (или пароль приложения, если включена 2FA)
DESTINATION_EMAIL = "itsm@domain.ru"    # Почта системы заявок (куда отправляем)

# --- OFFLINE QR MAILTO ---
MAIL_TO = os.getenv("MAIL_TO", DESTINATION_EMAIL)
