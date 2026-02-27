# config.py
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (если он существует)
load_dotenv()

# --- НАСТРОЙКИ ИНТЕРФЕЙСА ---
THEME_MODE = "light"      # "light", "dark", "system"
THEME_COLOR = "blue"      # "blue", "green", "dark-blue"
APP_TITLE = "AURORA.GERMES"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


# --- ПАРАМЕТРЫ ПОЧТЫ (SMTP) ---
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = _env_int("SMTP_PORT", 465)
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
MAIL_TO = os.getenv("MAIL_TO", "")
MAIL_FROM = os.getenv("MAIL_FROM", SMTP_USER)
SMTP_USE_SSL = _env_bool("SMTP_USE_SSL", True)
SMTP_USE_STARTTLS = _env_bool("SMTP_USE_STARTTLS", False)

# --- Совместимость со старыми именами настроек ---
SMTP_SERVER = SMTP_HOST
SMTP_LOGIN = SMTP_USER
SMTP_PASSWORD = SMTP_PASS
DESTINATION_EMAIL = MAIL_TO
