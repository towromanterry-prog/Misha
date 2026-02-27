# qr_tools.py
import urllib.parse
import qrcode
from PIL import Image

def generate_telegram_qr(report_text, token, chat_id, max_len=450):
    """Создает QR-код со ссылкой для API Telegram и возвращает объект PIL Image"""
    
    # Обрезаем текст для стабильности QR
    safe_report = report_text if len(report_text) <= max_len else report_text[:max_len] + "..."
    
    # Формируем URL
    encoded_text = urllib.parse.quote(safe_report)
    full_url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={encoded_text}"

    # Генерируем картинку
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=4)
    qr.add_data(full_url)
    qr.make(fit=True)
    
    qr_wrapper = qr.make_image(fill_color="black", back_color="white")
    return qr_wrapper.get_image() # Возвращаем чистый PIL Image