# logger.py
import logging
import sys
import os

def get_executable_dir():
    """Умное определение пути (работает и для скрипта, и для EXE от PyInstaller)"""
    if getattr(sys, 'frozen', False):
        # Если запущено как скомпилированный EXE
        return os.path.dirname(sys.executable)
    else:
        # Если запущено как обычный .py скрипт
        return os.path.dirname(os.path.abspath(__file__))

# Формируем путь к файлу лога
LOG_FILE = os.path.join(get_executable_dir(), "diag_tool.log")

def get_logger(module_name="DiagApp"):
    """Создает и возвращает настроенный логгер"""
    logger = logging.getLogger(module_name)
    
    # Чтобы логгер не дублировал записи при повторном вызове
    if not logger.handlers:
        logger.setLevel(logging.DEBUG) # Логируем всё: от DEBUG до CRITICAL
        
        # Настраиваем запись в файл (с поддержкой русского языка)
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Формат: Время | Уровень | Модуль | Сообщение
        formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | [%(module)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
    return logger