import flet as ft
import asyncio
import os
import sys
import socket
import psutil
from datetime import datetime
import functools
import subprocess
import base64

import system_net_tools as snt
import config
import logger
import email_sender


log = logger.get_logger(__name__)


def ui_error_message(text: str) -> str:
    return f"Ошибка: {text}"


def get_image_base64(filename):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    path = os.path.join(base_path, filename)
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return None

async def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    pfunc = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(None, pfunc)

def get_engineer_content(page: ft.Page):
    # --- ПРЕДОХРАНИТЕЛЬ ---
    logo_b64 = get_image_base64("logo.png")
    if logo_b64:
        header = ft.Image(src_base64=logo_b64, width=400, height=80, fit=ft.ImageFit.CONTAIN)
    else:
        header = ft.Text("AURORA.GERMES", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700)

    info_textbox = ft.TextField(
        multiline=True,
        read_only=True,
        min_lines=15,
        max_lines=15,
        text_size=13,
        text_style=ft.TextStyle(font_family="RobotoMono"),
        expand=True,
        border_color=ft.colors.BLUE_400
    )

    eng_terminal_list = ft.ListView(
        expand=True, 
        spacing=4, 
        auto_scroll=True
    )
    
    eng_terminal = ft.Container(
        content=eng_terminal_list,
        bgcolor=ft.colors.BLACK87,
        border_radius=4,
        padding=10,
        expand=True
    )

    target_input = ft.TextField(label="IP адрес или Узел (для Ping / Tracert)", value="ya.ru", width=300, height=40)
    ticket_input = ft.TextField(label="Введите номер заявки", width=200, height=40)
    
    eng_progress = ft.ProgressBar(visible=False, color=ft.colors.RED)

    def log_to_eng_term(text):
        current_time = datetime.now().strftime("%H:%M:%S")
        eng_terminal_list.controls.append(
            ft.Text(f"[{current_time}] {text}", font_family="RobotoMono", color=ft.colors.GREEN_400, size=13, selectable=True)
        )
        page.update()

    async def send_email_log(e):
        ticket_num = ticket_input.value.strip()
        if not ticket_num:
            log_to_eng_term(f"❌ {ui_error_message('укажите номер заявки перед отправкой!')}")
            page.snack_bar = ft.SnackBar(ft.Text(ui_error_message("пожалуйста, введите номер заявки!")), bgcolor=ft.colors.ERROR)
            page.snack_bar.open = True
            page.update()
            return
            
        e.control.disabled = True
        eng_progress.visible = True
        log_to_eng_term("⏳ Формирование отчета и подключение к почтовому серверу...")
        page.update()

        pc_info = info_textbox.value if info_textbox.value else "Данные о ПК не собирались."
        
        terminal_lines = []
        for ctrl in eng_terminal_list.controls:
            if hasattr(ctrl, 'value'):
                terminal_lines.append(ctrl.value)
        terminal_text = "\n".join(terminal_lines) if terminal_lines else "Терминал пуст."
        
        report_text = (
            f"========================================\n"
            f"ОТЧЕТ ИНЖЕНЕРА (Номер заявки: {ticket_num})\n"
            f"Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"========================================\n\n"
            f"{pc_info}\n\n"
            f"========================================\n"
            f"[ ВЫВОД ИНЖЕНЕРНОГО ТЕРМИНАЛА ]\n"
            f"========================================\n"
            f"{terminal_text}\n"
        )

        try:
            await run_in_thread(
                email_sender.send_report_smtp,
                f"Диагностика рабочего места по заявке {ticket_num}",
                report_text,
                "engineer_report.txt",
                report_text.encode("utf-8"),
            )
            log_to_eng_term(f"✅ Лог успешно отправлен в заявку {ticket_num} на {config.DESTINATION_EMAIL}")
            page.snack_bar = ft.SnackBar(ft.Text("Письмо успешно отправлено!"), bgcolor=ft.colors.GREEN)
            ticket_input.value = ""
        except Exception as ex:
            message = ui_error_message(f"ошибка отправки почты: {ex}")
            log_to_eng_term(f"❌ {message}")
            log.error(message)
            page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=ft.colors.ERROR)
        finally:
            e.control.disabled = False
            eng_progress.visible = False
            page.snack_bar.open = True
            page.update()

    def save_engineer_log(e):
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Инженерный_Лог_{date_str}.txt"
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        file_path = os.path.join(logs_dir, filename)
        
        pc_info = info_textbox.value if info_textbox.value else "Данные о ПК не собирались."
        
        terminal_lines = []
        for ctrl in eng_terminal_list.controls:
            if hasattr(ctrl, 'value'):
                terminal_lines.append(ctrl.value)
        terminal_text = "\n".join(terminal_lines) if terminal_lines else "Терминал пуст."
        
        report_text = (
            f"========================================\n"
            f"ОТЧЕТ ИНЖЕНЕРА (Создан: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
            f"========================================\n\n"
            f"{pc_info}\n\n"
            f"========================================\n"
            f"[ ВЫВОД ИНЖЕНЕРНОГО ТЕРМИНАЛА ]\n"
            f"========================================\n"
            f"{terminal_text}\n"
        )

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            
            log_to_eng_term(f"✅ Лог сохранен: {filename}")
            
            page.snack_bar = ft.SnackBar(ft.Text(f"Лог успешно сохранен в папку logs!"), bgcolor=ft.colors.GREEN)
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            message = ui_error_message(f"ошибка при сохранении лога: {ex}")
            log_to_eng_term(f"❌ {message}")
            log.error(message)

    async def gather_pc_info(e):
        e.control.disabled = True
        eng_progress.visible = True
        info_textbox.value = "Сбор диагностических данных ПК (пожалуйста, подождите)...\n"
        page.update()

        try:
            pc_name = socket.gethostname()
            logged_user = os.getlogin() if hasattr(os, 'getlogin') else "Неизвестно"
            
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except:
                local_ip = "Не определен"

            mac_addr = await run_in_thread(snt.get_mac_address)
            ext_ip = await run_in_thread(snt.get_external_ip)
            domain_info = await run_in_thread(snt.get_domain_controller)
            gateway = await run_in_thread(snt.get_gateway)
            
            firewall_status = await run_in_thread(snt.run_command_args, ["netsh", "advfirewall", "show", "allprofiles", "state"], 5)
            fw_clean = "Включен" if "ON" in firewall_status.upper() or "ВКЛ" in firewall_status.upper() else "Отключен или не удалось определить"

            av_status = await run_in_thread(snt.run_command_args, ["powershell", "-NoProfile", "-Command", "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct | Select-Object -ExpandProperty displayName"], 5)
            if not av_status: av_status = "Не найден (или Windows Defender)"

            last_update = await run_in_thread(snt.run_command_args, ["powershell", "-NoProfile", "-Command", "(Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 1).InstalledOn"], 10)

            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            uptime_str = f"{uptime.days} дн., {uptime.seconds // 3600} час., {(uptime.seconds // 60) % 60} мин."

            ping_gw = await run_in_thread(snt.get_ping_status, gateway) if gateway != "Не найден" else "N/A"
            ping_ya = await run_in_thread(snt.get_ping_status, "ya.ru")
            
            dc_name = domain_info.split()[0] if domain_info and "Не найден" not in domain_info else None
            trace_dc = "ПК не в домене"
            if dc_name:
                info_textbox.value += "\nВыполнение трассировки до Домен-контроллера...\n"
                page.update()
                trace_dc = await run_in_thread(snt.run_command_args, ["tracert", "-d", "-h", "5", "-w", "1000", dc_name], 15)

            report = f"""[ ИНФОРМАЦИЯ О ПК И СИСТЕМЕ ]
Залогиненный пользователь : {logged_user}
Домен / Контроллер        : {domain_info}
IP адрес локальный        : {local_ip}
MAC-адрес                 : {mac_addr}
Внешний IP адрес (WAN)    : {ext_ip}

[ БЕЗОПАСНОСТЬ И ОС ]
Статус Файрволла          : {fw_clean}
Статус Антивируса         : {av_status.replace(chr(10), ', ').strip()}
Дата последнего обновления: {last_update.strip()}
Время работы ОС (Аптайм)  : {uptime_str}

[ БАЗОВАЯ СЕТЬ ]
Пинг до Шлюза ({gateway}) : {ping_gw}
Пинг до ya.ru             : {ping_ya}

[ ТРАССИРОВКА ДО КОНТРОЛЛЕРА ДОМЕНА ]
{trace_dc.strip()}
"""
            info_textbox.value = report

        except Exception as ex:
            message = ui_error_message(f"ошибка при сборе данных: {ex}")
            info_textbox.value = message
            log.error(message)
        finally:
            e.control.disabled = False
            eng_progress.visible = False
            page.update()

    def open_event_viewer(e):
        log_to_eng_term("Запуск Просмотра событий (eventvwr.msc)...")
        subprocess.Popen(["eventvwr.msc"], shell=False)

    async def run_route_print(e):
        log_to_eng_term("Выполнение route print...")
        res = await run_in_thread(snt.run_command_args, ["route", "print"], 10)
        log_to_eng_term(f"Результат:\n{res}")

    async def run_netstat(e):
        log_to_eng_term("Получение прослушиваемых портов...")
        res = await run_in_thread(snt.run_command_shell, "netstat -ano | findstr LISTENING", 10)
        log_to_eng_term(f"Результат (LISTENING):\n{res}")

    async def run_custom_ping(e):
        target = target_input.value.strip()
        if not target: return
        log_to_eng_term(f"Выполнение ping {target}...")
        res = await run_in_thread(snt.run_command_args, ["ping", target], 15)
        log_to_eng_term(f"Результат:\n{res}")

    async def run_custom_tracert(e):
        target = target_input.value.strip()
        if not target: return
        log_to_eng_term(f"Выполнение tracert -d {target}...")
        res = await run_in_thread(snt.run_command_args, ["tracert", "-d", target], 30)
        log_to_eng_term(f"Результат:\n{res}")

    async def run_flushdns(e):
        log_to_eng_term("Выполнение ipconfig /flushdns...")
        res = await run_in_thread(snt.run_command_args, ["ipconfig", "/flushdns"], 5)
        log_to_eng_term(f"Результат:\n{res}")

    btn_style = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4))
    
    tools_row_1 = ft.Row([
        ft.ElevatedButton("Просмотр логов (Windows)", icon=ft.Icons.MANAGE_SEARCH, on_click=open_event_viewer, style=btn_style),
        ft.ElevatedButton("Таблица маршрутов (Route Print)", icon=ft.Icons.ROUTE, on_click=run_route_print, style=btn_style),
        ft.ElevatedButton("Прослушиваемые порты", icon=ft.Icons.SECURITY, on_click=run_netstat, style=btn_style),
        ft.ElevatedButton("FlushDNS", icon=ft.Icons.DELETE_SWEEP, on_click=run_flushdns, style=btn_style),
    ], wrap=True)

    tools_row_2 = ft.Row([
        target_input,
        ft.ElevatedButton("Выполнить Ping", icon=ft.Icons.NETWORK_CHECK, on_click=run_custom_ping, style=btn_style, bgcolor=ft.colors.BLUE_50, color=ft.colors.BLUE_900),
        ft.ElevatedButton("Выполнить Tracert (-d)", icon=ft.Icons.CALL_SPLIT, on_click=run_custom_tracert, style=btn_style, bgcolor=ft.colors.BLUE_50, color=ft.colors.BLUE_900),
    ])

    top_actions_row = ft.Row([
        ticket_input,
        ft.ElevatedButton("Отправить в заявку", icon=ft.Icons.FORWARD_TO_INBOX, on_click=send_email_log, bgcolor=ft.colors.ORANGE_700, color=ft.colors.WHITE),
        ft.ElevatedButton("Создать лог файл", icon=ft.Icons.SAVE, on_click=save_engineer_log, bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE),
        ft.ElevatedButton("Собрать данные ПК", icon=ft.Icons.REFRESH, on_click=gather_pc_info, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)
    ], wrap=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    content = ft.Column([
        header, 
        ft.Divider(),
        ft.Text("Информация о ПК и Сети", size=20, weight=ft.FontWeight.BOLD),
        top_actions_row, 
        eng_progress,
        info_textbox,
        ft.Divider(),
        ft.Text("Инструменты диагностики", size=20, weight=ft.FontWeight.BOLD),
        tools_row_1,
        tools_row_2,
        eng_terminal 
    ], expand=True, scroll=ft.ScrollMode.AUTO)

    return content
