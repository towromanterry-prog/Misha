import subprocess
import socket
import urllib.request
import platform
import re
import psutil
import os


ALLOWED_SHELL_COMMANDS = {
    "netstat -ano | findstr LISTENING",
}

# --- СЛОВАРЬ С ПУТЯМИ К ПРОГРАММАМ УДАЛЕННОГО ДОСТУПА ---
# Программа проверит все варианты путей (x86, x64, AppData пользователя)
REMOTE_APPS_PATHS = {
    "AnyDesk": [
        r"C:\Program Files (x86)\AnyDesk\AnyDesk.exe",
        r"C:\Program Files\AnyDesk\AnyDesk.exe",
        os.path.expandvars(r"%APPDATA%\AnyDesk\AnyDesk.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\AnyDesk\AnyDesk.exe")
    ],
    "RuDesktop": [
        r"C:\Program Files\RuDesktop\RuDesktop.exe",
        r"C:\Program Files (x86)\RuDesktop\RuDesktop.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\RuDesktop\RuDesktop.exe")
    ],
    "Ассистент": [
        r"C:\Program Files\SAFIB\Assistant\Assistant.exe",
        r"C:\Program Files (x86)\SAFIB\Assistant\Assistant.exe",
        r"C:\Program Files\Assistant\Assistant.exe",
        r"C:\Program Files (x86)\Assistant\Assistant.exe"
    ],
    "RMS": [
        r"C:\Program Files (x86)\Remote Manipulator System - Host\rutserv.exe",
        r"C:\Program Files\Remote Manipulator System - Host\rutserv.exe",
        r"C:\Program Files (x86)\Remote Manipulator System - Viewer\rutview.exe",
        r"C:\Program Files\Remote Manipulator System - Viewer\rutview.exe"
    ]
}

def scan_remote_apps():
    """Сканирует систему и возвращает словарь найденных программ: {Имя: Путь}"""
    found_apps = {}
    if platform.system().lower() == "windows":
        for app_name, paths in REMOTE_APPS_PATHS.items():
            for app_path in paths:
                if os.path.exists(app_path):
                    found_apps[app_name] = app_path
                    break # Переходим к следующей программе, если эта уже найдена
    return found_apps

def decode_command_output(raw_output):
    """Декодирует байты консольного вывода: utf-8 -> cp866 -> cp1251."""
    raw_output = raw_output or b""
    for encoding in ("utf-8", "cp866", "cp1251"):
        try:
            return raw_output.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_output.decode("cp1251", errors="replace")


def run_command_args(args: list[str], timeout_sec: int = 15) -> str:
    """Безопасный запуск команды списком аргументов (shell=False)."""
    try:
        result = subprocess.run(
            args,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_sec
        )
        text = decode_command_output(result.stdout)
        return text.strip()

    except subprocess.TimeoutExpired as e:
        text = decode_command_output(e.stdout)
        return f"{text.strip()}\n\n[!] Превышено время ожидания ({timeout_sec} сек.). Показан частичный результат."
    except Exception as e:
        return f"Ошибка выполнения команды: {str(e)}"


def run_command_shell(cmd: str, timeout_sec: int = 15) -> str:
    """Запуск shell-команды только из жестко зафиксированного списка."""
    normalized_cmd = cmd.strip()
    if normalized_cmd not in ALLOWED_SHELL_COMMANDS:
        return "Ошибка выполнения команды: shell=True разрешён только для фиксированных команд"

    try:
        result = subprocess.run(
            normalized_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_sec
        )
        return decode_command_output(result.stdout).strip()
    except subprocess.TimeoutExpired as e:
        text = decode_command_output(e.stdout)
        return f"{text.strip()}\n\n[!] Превышено время ожидания ({timeout_sec} сек.). Показан частичный результат."
    except Exception as e:
        return f"Ошибка выполнения команды: {str(e)}"

def check_online():
    """Проверяет наличие интернета путем быстрого подключения к DNS Google"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def get_external_ip():
    """Получает внешний IP, используя несколько сервисов для надежности"""
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com"
    ]
    
    for url in services:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.read().decode('utf-8').strip()
        except:
            continue
            
    return "Не определен"

def get_mac_address():
    """Получает MAC-адрес активного интерфейса через psutil"""
    try:
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                # psutil.AF_LINK соответствует MAC-адресам
                if addr.family == psutil.AF_LINK:
                    return addr.address.upper().replace(':', '-')
    except Exception:
        pass
    return "Не определен"

def get_gateway():
    """Определяет шлюз по умолчанию (Windows)"""
    if platform.system().lower() == "windows":
        output = run_command_args(["route", "print", "0.0.0.0"], timeout_sec=5)
        # Ищем строку вида "0.0.0.0   0.0.0.0   192.168.1.1"
        match = re.search(r'0\.0\.0\.0\s+0\.0\.0\.0\s+([0-9\.]+)', output)
        if match:
            return match.group(1)
    return "Не найден"

def get_domain_controller():
    """Определяет контроллер домена через переменную окружения LOGONSERVER"""
    if platform.system().lower() != "windows":
        return "Не найден (Не Windows)"
        
    output = os.environ.get("LOGONSERVER", "").strip()
    
    # Если ПК не в домене, он вернет саму строку "%LOGONSERVER%"
    if output and output.strip() != "%LOGONSERVER%":
        return output.strip('\\ \r\n')
        
    return "Не найден"

def get_ping_status(host):
    """Выполняет один запрос ping к узлу и возвращает статус"""
    if not host or host == "N/A" or host == "Не найден":
        return "N/A"
        
    if platform.system().lower() == "windows":
        command_args = ["ping", "-n", "1", host]
    else:
        command_args = ["ping", "-c", "1", host]

    output = run_command_args(command_args, timeout_sec=5)
    
    if "TTL=" in output or "ttl=" in output.lower():
        return "OK"
    return "Недоступен"

def run_mtr(host="ya.ru", duration=15):
    """
    Выполняет MTR (My traceroute).
    Если mtr не установлен (Windows), использует ускоренный tracert в качестве резервы.
    """
    timeout = duration + 5 # Даем запас времени сверх указанной длительности
    
    if platform.system().lower() == "windows":
        result = run_command_args(["mtr", "-r", "-c", str(duration), host], timeout_sec=timeout)
        
        # Перехватываем сообщение Windows об отсутствии утилиты
        if not result or "не является" in result.lower() or "not recognized" in result.lower():
            # Запускаем tracert: -d (без DNS имен), -h 15 (прыжков), -w 1000 (таймаут 1 сек)
            fallback_cmd = ["tracert", "-d", "-h", "15", "-w", "1000", host]
            return run_command_args(fallback_cmd, timeout_sec=25)
        return result
    else:
        # Для Linux / macOS (тут mtr обычно есть)
        return run_command_args(["mtr", "-r", "-c", str(duration), host], timeout_sec=timeout)

def launch_app(app_path):
    """Асинхронный запуск программы без блокировки основного окна"""
    try:
        # Используем Popen для запуска процесса в фоне
        subprocess.Popen([app_path], shell=False)
        return True, ""
    except Exception as e:
        return False, f"Ошибка запуска: {str(e)}"
        
def get_default_adapter_info():
    """Возвращает информацию только об адаптере с маршрутом 0.0.0.0 (шлюзом по умолчанию)"""
    if platform.system().lower() == "windows":
        # Используем PowerShell: находим маршрут 0.0.0.0, берем его индекс и выводим свойства адаптера
        script = (
            "$route = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Select-Object -First 1; "
            "if ($route) { "
            "Get-NetAdapter -InterfaceIndex $route.ifIndex | Format-List Name, InterfaceDescription, Status "
            "} else { "
            "Write-Output 'Адаптер с маршрутом 0.0.0.0 (шлюзом по умолчанию) не найден.' "
            "}"
        )
        return run_command_args(["powershell", "-NoProfile", "-Command", script], timeout_sec=15)
    return "Не поддерживается на данной ОС"
