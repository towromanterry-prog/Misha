import flet as ft
import asyncio
import os
import sys
import socket
from datetime import datetime
import functools
import base64
from io import BytesIO

import config
import system_net_tools as snt
import logger
import report_builder
import qr_tools
import email_sender
import storage

import main_foreng

log = logger.get_logger(__name__) if hasattr(logger, 'get_logger') else logger


def get_image_base64(filename):
    """Находит картинку в .exe и кодирует её в Base64"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, filename)
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    return None

async def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    pfunc = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(None, pfunc)

def main(page: ft.Page):
    page.title = "AURORA.GERMES"
    page.window.width = 1150
    page.window.height = 1000
    page.theme_mode = ft.ThemeMode.LIGHT if config.THEME_MODE == "light" else ft.ThemeMode.DARK
    page.padding = 30
    
    page.fonts = {
        "RobotoMono": "https://github.com/google/fonts/raw/main/apache/robotomono/RobotoMono-Regular.ttf"
    }

    user_profile = storage.load_user_profile()

    # --- ЭЛЕМЕНТЫ ВКЛАДКИ "ДИАГНОСТИКА" ---
    contact_info = ft.Column([
        ft.Text("вы можете связаться с нами:", size=12, color=ft.colors.ON_SURFACE_VARIANT, italic=True),
        ft.Row([
            ft.Icon(ft.Icons.EMAIL, size=16, color=ft.colors.BLUE_700),
            ft.Text("help.it-aurora.ru", size=14, weight=ft.FontWeight.W_500)
        ], alignment=ft.MainAxisAlignment.END, spacing=5),
        ft.Row([
            ft.Icon(ft.Icons.PHONE, size=16, color=ft.colors.BLUE_700),
            ft.Text("+78123095404", size=14, weight=ft.FontWeight.W_500)
        ], alignment=ft.MainAxisAlignment.END, spacing=5)
    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END)

    # --- ПРЕДОХРАНИТЕЛЬ: Загружаем логотип или показываем текст ---
    logo_b64 = get_image_base64("logo.png")
    if logo_b64:
        header_left = ft.Image(src_base64=logo_b64, width=400, height=80, fit=ft.ImageFit.CONTAIN)
    else:
        # Если картинка потерялась при сборке, покажем красивый текст, чтобы не было ошибки
        header_left = ft.Text("AURORA.GERMES", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700)

    header_row = ft.Row(
        [header_left, contact_info], 
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER 
    )

    welcome_text = ft.Text("Вас приветствует программа для самодиагностики и запроса помощи.", size=16, color=ft.colors.ON_SURFACE_VARIANT)

    name_field = ft.TextField(label="ФИО", value=user_profile.get("name", ""), prefix_icon=ft.Icons.PERSON, expand=True)
    company_field = ft.TextField(label="Компания", value=user_profile.get("company", ""), prefix_icon=ft.Icons.BUSINESS, expand=True)
    saved_phone = user_profile.get("phone", "")
    phone_field = ft.TextField(label="Номер телефона", value=saved_phone if saved_phone else "+7", prefix_icon=ft.Icons.PHONE, expand=True)
    itsm_field = ft.TextField(label="Ваш ITSM логин", value=user_profile.get("itsm", ""), prefix_icon=ft.Icons.CONFIRMATION_NUMBER, expand=True)
    anydesk_field = ft.TextField(label="ID Удаленного доступа", prefix_icon=ft.Icons.COMPUTER, expand=True)
    problem_field = ft.TextField(label="Пожалуйста кратко опишите вашу проблему.", multiline=True, min_lines=3, max_lines=3, prefix_icon=ft.Icons.WARNING)

    progress_bar = ft.ProgressBar(width=400, color=ft.colors.BLUE, visible=False)
    progress_text = ft.Text("Ожидание запуска...", italic=True, visible=False)

    log_view = ft.ListView(expand=True, spacing=5, auto_scroll=True, height=250)
    log_container = ft.Container(content=log_view, border=ft.border.all(1, ft.colors.OUTLINE), border_radius=10, padding=10, bgcolor=ft.colors.SURFACE_VARIANT)

    def log_to_gui(msg, color=ft.colors.ON_SURFACE_VARIANT):
        current_time = datetime.now().strftime("%H:%M:%S")
        log_view.controls.append(ft.Text(f"[{current_time}] {msg}", font_family="RobotoMono", size=12, color=color))
        page.update()
        if hasattr(log, 'info'): log.info(msg)

    installed_remote_apps = snt.scan_remote_apps()
    remote_buttons = []
    if installed_remote_apps:
        for app_name, app_path in installed_remote_apps.items():
            def create_launch_handler(path, name):
                def handler(e):
                    success, msg = snt.launch_app(path)
                    if success: log_to_gui(f"🚀 Запущена программа: {name}", ft.colors.BLUE)
                    else: log_to_gui(f"❌ {msg}", ft.colors.RED)
                return handler
            icon_map = {"AnyDesk": ft.Icons.CAST_CONNECTED, "RuDesktop": ft.Icons.DESKTOP_WINDOWS, "Ассистент": ft.Icons.SUPPORT_AGENT, "RMS": ft.Icons.SETTINGS_REMOTE}
            btn = ft.FilledButton(text=app_name, icon=icon_map.get(app_name, ft.Icons.COMPUTER), on_click=create_launch_handler(app_path, app_name), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), bgcolor=ft.colors.SECONDARY))
            remote_buttons.append(btn)
        remote_ui_section = ft.Column([
            ft.Text("На Вашем компьютере обнаружены следующие программы удаленного доступа. Пожалуйста, запустите одну из них и впишите цифры из поля Это рабочее место/Ваш рабочий стол в поле ID Удаленного доступа. Пароль нужно будет сообщить сотруднику по телефону.", weight=ft.FontWeight.W_500, color=ft.colors.PRIMARY),
            ft.Row(remote_buttons, wrap=True)
        ])
    else:
        remote_ui_section = ft.Text("Программы удаленного доступа не найдены", italic=True, color=ft.colors.OUTLINE)

    qr_image = ft.Image(width=250, height=250, visible=False, fit=ft.ImageFit.CONTAIN)
    internet_status_text = ft.Text("Интернет: неизвестно", weight=ft.FontWeight.W_600, color=ft.colors.ON_SURFACE_VARIANT)
    sidebar_status_text = ft.Text("Заполните форму и нажмите кнопку отправки.", text_align=ft.TextAlign.CENTER, color=ft.colors.ON_SURFACE_VARIANT)
    sidebar = ft.Container(
        content=ft.Column([
            ft.Text("Статус", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            internet_status_text,
            ft.Container(content=qr_image, alignment=ft.alignment.center),
            ft.Container(content=sidebar_status_text, alignment=ft.alignment.center, padding=ft.padding.only(top=10))
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=300, padding=20, border=ft.border.only(left=ft.border.BorderSide(1, ft.colors.OUTLINE)),
    )

    latest_online_report = ""
    latest_offline_report = ""
    is_online = False

    def apply_connectivity_state(online: bool):
        nonlocal is_online
        is_online = online
        if online:
            internet_status_text.value = "Интернет: есть"
            internet_status_text.color = ft.colors.GREEN
            btn_send_email.disabled = not bool(latest_online_report)
            btn_generate_qr.disabled = True
        else:
            internet_status_text.value = "Интернет: нет"
            internet_status_text.color = ft.colors.RED
            btn_send_email.disabled = True
            btn_generate_qr.disabled = not bool(latest_offline_report)

    async def refresh_connectivity_status():
        check_hosts = ["ya.ru", "help.it-aurora.ru", "pool.ntp.org"]
        failed_hosts = []
        for host in check_hosts:
            status = await run_in_thread(snt.get_ping_status, host)
            if status != "OK":
                failed_hosts.append(host)
        apply_connectivity_state(len(failed_hosts) < 3)
        return failed_hosts

    def save_diagnostic_report(report_text, name):
        safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c in " -_"]).rstrip()
        prefix = f"Диагностика_{safe_name}" if safe_name else "Диагностика"
        return storage.save_text_report(report_text, prefix)

    async def send_email_click(e):
        await refresh_connectivity_status()
        if not is_online:
            sidebar_status_text.value = "Интернет недоступен. Отправка email запрещена."
            sidebar_status_text.color = ft.colors.ERROR
            page.snack_bar = ft.SnackBar(ft.Text("Нет интернета: email не отправлен."), bgcolor=ft.colors.ERROR)
            page.snack_bar.open = True
            page.update()
            return

        if not latest_online_report:
            page.snack_bar = ft.SnackBar(ft.Text("Нет онлайн-отчета для отправки."), bgcolor=ft.colors.ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        btn_send_email.disabled = True
        page.update()
        try:
            subject = f"AURORA.GERMES отчет: {name_field.value or 'Пользователь'}"
            body = (
                "Добрый день.\n"
                "Во вложении полный диагностический отчет AURORA.GERMES.\n\n"
                f"{latest_online_report}"
            )
            await run_in_thread(
                email_sender.send_report_smtp,
                subject,
                body,
                "report.txt",
                latest_online_report.encode("utf-8"),
            )
            log_to_gui("✅ Отчет отправлен по email.", ft.colors.GREEN)
            sidebar_status_text.value = "✅ Отчет отправлен по email."
            sidebar_status_text.color = ft.colors.GREEN
            page.snack_bar = ft.SnackBar(ft.Text("Отчет отправлен по email."), bgcolor=ft.colors.GREEN)
        except Exception as exc:
            message = f"Не удалось отправить email: {exc}"
            log_to_gui(f"❌ {message}", ft.colors.RED)
            sidebar_status_text.value = message
            sidebar_status_text.color = ft.colors.RED
            page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=ft.colors.ERROR)
        finally:
            await refresh_connectivity_status()
            page.snack_bar.open = True
            page.update()

    async def generate_qr_click(e):
        await refresh_connectivity_status()
        if is_online:
            sidebar_status_text.value = "QR недоступен при активном интернете."
            sidebar_status_text.color = ft.colors.ORANGE
            page.snack_bar = ft.SnackBar(ft.Text("Интернет доступен: QR не предлагается."), bgcolor=ft.colors.ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        if not latest_offline_report:
            page.snack_bar = ft.SnackBar(ft.Text("Нет офлайн-отчета для генерации QR."), bgcolor=ft.colors.ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        max_body_len = 1600
        report_for_mail = latest_offline_report if len(latest_offline_report) <= max_body_len else latest_offline_report[: max_body_len - 22].rstrip() + "\n\n[TRUNCATED]"
        if len(report_for_mail) < len(latest_offline_report):
            log_to_gui("⚠️ Текст отчета для mailto был безопасно сокращен.", ft.colors.ORANGE)
        mailto_url = qr_tools.build_mailto(
            config.MAIL_TO,
            "AURORA.GERMES OFFLINE",
            report_for_mail,
        )
        qr_pil = qr_tools.generate_qr_image(mailto_url)
        qr_buffer = BytesIO()
        qr_pil.save(qr_buffer, format="PNG")
        qr_image.src_base64 = base64.b64encode(qr_buffer.getvalue()).decode("utf-8")
        qr_image.visible = True
        sidebar_status_text.value = "⚠️ Офлайн-режим: QR для отправки отчета сгенерирован."
        sidebar_status_text.color = ft.colors.ERROR
        page.snack_bar = ft.SnackBar(ft.Text("QR сформирован."), bgcolor=ft.colors.GREEN)
        page.snack_bar.open = True
        page.update()

    def clear_profile_click(e):
        storage.clear_user_profile()
        name_field.value = ""
        company_field.value = ""
        phone_field.value = "+7"
        itsm_field.value = ""
        page.snack_bar = ft.SnackBar(ft.Text("Профиль очищен."), bgcolor=ft.colors.BLUE_GREY)
        page.snack_bar.open = True
        page.update()

    async def run_logic(e):
        nonlocal latest_online_report, latest_offline_report
        if not name_field.value or not problem_field.value:
            page.snack_bar = ft.SnackBar(ft.Text("Ошибка: Заполните ФИО и Описание проблемы!"), bgcolor=ft.colors.ERROR)
            page.snack_bar.open = True
            page.update()
            return
        storage.save_user_profile({"name": name_field.value, "company": company_field.value, "phone": phone_field.value, "itsm": itsm_field.value})
        btn_submit.disabled = True
        progress_bar.visible = True
        progress_text.visible = True
        log_view.controls.clear()
        qr_image.visible = False
        sidebar_status_text.value = "Выполнение диагностики..."
        latest_online_report = ""
        latest_offline_report = ""
        btn_send_email.disabled = True
        btn_generate_qr.disabled = True
        sidebar_status_text.color = ft.colors.ON_SURFACE_VARIANT
        log_to_gui("=== Запуск диагностики ===", ft.colors.BLUE)
        page.update()

        ext_ip = "N/A"
        mac_addr = "N/A"
        local_ip = "Не определен"
        pc_name = socket.gethostname()
        gateway = "N/A"
        domain_info = "N/A"

        try:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except: pass
            
            mac_addr = await run_in_thread(snt.get_mac_address)
            progress_text.value = "Предварительная проверка связи (3 узла)..."
            page.update()
            log_to_gui(">>> Предварительный пинг (ya.ru, help.it-aurora.ru, pool.ntp.org)...")
            
            failed_hosts = await refresh_connectivity_status()

            if len(failed_hosts) == 0:
                scenario = 1
                log_to_gui("✅ Все 3 узла доступны. Запуск СЦЕНАРИЯ 1.", ft.colors.GREEN)
            elif len(failed_hosts) < 3:
                scenario = 2
                log_to_gui(f"⚠️ Часть узлов недоступна ({', '.join(failed_hosts)}). Запуск СЦЕНАРИЯ 2.", ft.colors.ORANGE)
            else:
                scenario = 3
                log_to_gui("🆘 Все 3 узла недоступны. Запуск СЦЕНАРИЯ 3 (Полный офлайн).", ft.colors.RED)

            if scenario == 3:
                progress_text.value = "Сбор информации об адаптере 0.0.0.0 и трассировка..."
                page.update()
                log_to_gui(">>> Трассировка до 77.88.8.8 (первые 5 хопов)...", ft.colors.BLUE)
                report = await run_in_thread(report_builder.build_offline_hops_report)

                filepath, filename = save_diagnostic_report(report, name_field.value)
                latest_offline_report = report
                log_to_gui(f"✅ Отчет сохранен: {filename}", ft.colors.GREEN)
                sidebar_status_text.value = "⚠️ Нет связи. Отчет сохранен локально, доступна генерация QR."
                sidebar_status_text.color = ft.colors.ERROR
                btn_send_email.disabled = True
                btn_generate_qr.disabled = False
            else:
                progress_text.value = "Сбор сетевых настроек и полная маршрутизация..."
                page.update()
                gateway = await run_in_thread(snt.get_gateway)
                domain_info = await run_in_thread(snt.get_domain_controller)
                ext_ip = await run_in_thread(snt.get_external_ip)
                log_to_gui(">>> Пинг основных узлов...", ft.colors.BLUE)
                ping_gw = await run_in_thread(snt.get_ping_status, gateway) if gateway else "N/A"
                ping_8888 = await run_in_thread(snt.get_ping_status, "8.8.8.8")
                ping_1111 = await run_in_thread(snt.get_ping_status, "1.1.1.1")
                dc_name = domain_info.split()[0] if domain_info and "Не найден" not in domain_info else "N/A"
                ping_dc = await run_in_thread(snt.get_ping_status, dc_name) if dc_name != "N/A" else "N/A"
                nslookup_raw = await run_in_thread(snt.run_command_args, ["nslookup", "ya.ru"])
                nslookup_res = "OK" if "Address" in nslookup_raw else "Error"

                failed_host_traces = []
                if scenario == 2:
                    for fh in failed_hosts:
                        log_to_gui(f">>> Трассировка до недоступного узла: {fh}...", ft.colors.ORANGE)
                        fh_trace = await run_in_thread(snt.run_command_args, ["tracert", "-d", "-h", "15", "-w", "1000", fh], 25)
                        failed_host_traces.append({"host": fh, "trace": fh_trace})

                log_to_gui(">>> Запуск основного MTR до ya.ru...", ft.colors.BLUE)
                trace_res = await run_in_thread(snt.run_mtr, "ya.ru", 15)

                report_context = {
                    "scenario": scenario,
                    "name": name_field.value,
                    "company": company_field.value,
                    "phone": phone_field.value,
                    "itsm": itsm_field.value,
                    "problem": problem_field.value,
                    "anydesk": anydesk_field.value,
                    "pc_name": pc_name,
                    "local_ip": local_ip,
                    "ext_ip": ext_ip,
                    "mac_addr": mac_addr,
                    "domain_info": domain_info,
                    "gateway": gateway,
                    "dc_name": dc_name,
                    "ping_gw": ping_gw,
                    "ping_dc": ping_dc,
                    "ping_8888": ping_8888,
                    "ping_1111": ping_1111,
                    "nslookup_res": nslookup_res,
                    "failed_host_traces": failed_host_traces,
                    "trace_res": trace_res,
                }
                report_text = report_builder.build_full_report(report_context)
                body = "Добрый день.\nВо вложении полный диагностический отчет AURORA.GERMES.\n\n" + report_text
                filepath, filename = save_diagnostic_report(report_text, name_field.value)
                latest_online_report = report_text
                log_to_gui(f"Отчет сохранен: {filename}", ft.colors.GREEN)
                log_to_gui(f"Сопроводительное письмо подготовлено ({len(body)} символов).", ft.colors.BLUE)
                sidebar_status_text.value = "✅ Диагностика завершена. Можно отправить email с отчетом."
                sidebar_status_text.color = ft.colors.GREEN
                btn_send_email.disabled = False
                btn_generate_qr.disabled = True

        except Exception as e:
            log_to_gui(f"Критическая ошибка: {e}", ft.colors.RED)
            sidebar_status_text.value = "Произошла ошибка!"
            sidebar_status_text.color = ft.colors.RED
        finally:
            await refresh_connectivity_status()
            progress_bar.visible = False
            progress_text.value = "Диагностика завершена."
            btn_submit.disabled = False
            page.snack_bar = ft.SnackBar(ft.Text("Процесс завершен!"), bgcolor=ft.colors.GREEN)
            page.snack_bar.open = True
            page.update()

    btn_submit = ft.ElevatedButton("Собрать данные и Отправить заявку", icon=ft.Icons.SEND, on_click=run_logic, style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE, padding=20, shape=ft.RoundedRectangleBorder(radius=8)))
    btn_send_email = ft.ElevatedButton("Отправить email", icon=ft.Icons.EMAIL, disabled=True, on_click=send_email_click, style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE, padding=20, shape=ft.RoundedRectangleBorder(radius=8)))
    btn_generate_qr = ft.ElevatedButton("Сгенерировать QR", icon=ft.Icons.QR_CODE, disabled=True, on_click=generate_qr_click, style=ft.ButtonStyle(bgcolor=ft.colors.ORANGE_700, color=ft.colors.WHITE, padding=20, shape=ft.RoundedRectangleBorder(radius=8)))
    btn_clear_profile = ft.OutlinedButton("Очистить профиль", icon=ft.Icons.DELETE_OUTLINE, on_click=clear_profile_click)

    main_content = ft.Column([
        header_row, 
        welcome_text, ft.Divider(), remote_ui_section, ft.Divider(),
        ft.Row([name_field, company_field]), ft.Row([phone_field, itsm_field, anydesk_field]), problem_field, ft.Divider(),
        ft.Column([ft.Row([btn_submit, btn_send_email, btn_generate_qr], wrap=True), ft.Row([btn_clear_profile], alignment=ft.MainAxisAlignment.START), ft.Row([progress_bar], alignment=ft.MainAxisAlignment.START), progress_text]),
        ft.Text("Терминал выполнения:", weight=ft.FontWeight.W_500), log_container
    ], expand=True, scroll=ft.ScrollMode.AUTO) 

    tab_diag_content = ft.Row([main_content, sidebar], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)

    tab_eng_content = main_foreng.get_engineer_content(page)

    content_diag = ft.Container(content=tab_diag_content, padding=ft.padding.only(top=15), visible=True, expand=True)
    content_eng = ft.Container(content=tab_eng_content, padding=ft.padding.only(top=15), visible=False, expand=True)

    def change_tab(e):
        if e.control.data == "diag":
            content_diag.visible = True
            content_eng.visible = False
            btn_diag.style.color = ft.colors.BLUE_700
            btn_diag.style.bgcolor = ft.colors.BLUE_50
            btn_eng.style.color = ft.colors.ON_SURFACE
            btn_eng.style.bgcolor = ft.colors.TRANSPARENT
        else:
            content_diag.visible = False
            content_eng.visible = True
            btn_diag.style.color = ft.colors.ON_SURFACE
            btn_diag.style.bgcolor = ft.colors.TRANSPARENT
            btn_eng.style.color = ft.colors.BLUE_700
            btn_eng.style.bgcolor = ft.colors.BLUE_50
        page.update()

    btn_diag = ft.TextButton(
        text="Диагностика", 
        icon=ft.Icons.HEALTH_AND_SAFETY, 
        data="diag", 
        on_click=change_tab,
        style=ft.ButtonStyle(
            color=ft.colors.BLUE_700, 
            bgcolor=ft.colors.BLUE_50,
            shape=ft.RoundedRectangleBorder(radius=8)
        )
    )
    
    btn_eng = ft.TextButton(
        text="Для Инженера", 
        icon=ft.Icons.ENGINEERING, 
        data="eng", 
        on_click=change_tab,
        style=ft.ButtonStyle(
            color=ft.colors.ON_SURFACE,
            bgcolor=ft.colors.TRANSPARENT,
            shape=ft.RoundedRectangleBorder(radius=8)
        )
    )

    custom_tabs = ft.Row([btn_diag, btn_eng], spacing=10)

    page.add(
        custom_tabs,
        ft.Divider(height=1),
        content_diag,
        content_eng
    )

    page.run_task(refresh_connectivity_status)

if __name__ == "__main__":
    ft.app(target=main)
