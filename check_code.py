#!/usr/bin/env python3
import sys
print('=' * 60)
print('✓ ПРОВЕРКА КОДА')
print('=' * 60)

# Проверка импортов
print('\n1. Проверка импортов:')
modules = ['customtkinter', 'requests', 'psutil', 'qrcode', 'dotenv', 'PIL']
for mod in modules:
    try:
        __import__(mod)
        print(f'   ✅ {mod}')
    except ImportError as e:
        print(f'   ❌ {mod}: {str(e)[:50]}')

# Проверка конфига
print('\n2. Проверка конфигурации:')
try:
    import config
    print('   ✅ config.py загружается')
    print(f'      APP_TITLE: {config.APP_TITLE}')
    has_token = bool(config.TG_TOKEN)
    has_chat = bool(config.TG_CHAT_ID)
    print(f'      TG_TOKEN: {"✅ установлен" if has_token else "❌ не установлен"}')
    print(f'      TG_CHAT_ID: {"✅ установлен" if has_chat else "❌ не установлен"}')
except Exception as e:
    print(f'   ❌ config.py: {str(e)[:50]}')

# Проверка модулей приложения
print('\n3. Проверка модулей приложения:')
app_modules = ['logger', 'system_net_tools', 'qr_tools']
for mod in app_modules:
    try:
        __import__(mod)
        print(f'   ✅ {mod}.py')
    except Exception as e:
        print(f'   ❌ {mod}.py: {str(e)[:50]}')

# Проверка main.py
print('\n4. Проверка main.py:')
try:
    import main
    print('   ✅ main.py загружается успешно')
except Exception as e:
    print(f'   ❌ main.py: {str(e)[:100]}')

print('\n' + '=' * 60)
print('✅ ПРОВЕРКА ЗАВЕРШЕНА')
print('=' * 60)
