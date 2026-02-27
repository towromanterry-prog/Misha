import re
from typing import Any

import system_net_tools as snt
import qr_tools


def run_command_args(args: list[str], timeout_sec: int = 15) -> str:
    """Безопасный запуск команды + нормализация вывода."""
    raw_output = snt.run_command_args(args, timeout_sec)
    return normalize_output(raw_output)


def normalize_output(output: str) -> str:
    """Единый вид вывода: LF, без лишних пробелов по краям строк."""
    normalized = (output or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(lines).strip()


def extract_first_hops(trace_output: str, max_hops: int = 5) -> str:
    """Извлекает только строки хопов из tracert-вывода."""
    hop_lines: list[str] = []
    for line in normalize_output(trace_output).split("\n"):
        if re.match(r"^\s*\d+\s+", line):
            hop_lines.append(line.strip())
        if len(hop_lines) >= max_hops:
            break

    if not hop_lines:
        return "Не удалось выделить хопы трассировки."

    return "\n".join(hop_lines)


def build_offline_hops_report() -> str:
    """Офлайн-отчёт: только первые 5 хопов до 77.88.8.8, без персональных данных."""
    trace_raw = run_command_args(["tracert", "-d", "-h", "5", "-w", "1000", "77.88.8.8"], timeout_sec=25)
    hops_block = qr_tools.extract_tracert_hops(trace_raw, max_hops=5) or "Не удалось выделить хопы трассировки."
    return "\n".join([
        "🆘 OFFLINE (СЦЕНАРИЙ 3)",
        "--- ТРАССИРОВКА (5 ХОПОВ ДО 77.88.8.8) ---",
        hops_block,
    ]).strip()


def build_full_report(context: dict[str, Any]) -> str:
    """Полный ONLINE-отчёт для email (сценарий 1/2)."""
    scenario = context.get("scenario", 1)
    header_text = "⚠️ ONLINE ЗАЯВКА (СЦЕНАРИЙ 2)" if scenario == 2 else "✅ ONLINE ЗАЯВКА (СЦЕНАРИЙ 1)"

    traces = context.get("failed_host_traces", [])
    trace_blocks = []
    for trace_item in traces:
        host = str(trace_item.get("host", "")).upper()
        trace_text = normalize_output(str(trace_item.get("trace", "")))
        trace_blocks.append(f"--- TRACE ДО {host} ---\n{trace_text}")

    traces_section = "\n\n".join(trace_blocks).strip()
    if traces_section:
        traces_section = f"\n{traces_section}\n"

    report = (
        f"{header_text}\n"
        f"👤 {context.get('name') or 'Не указано'}\n"
        f"🏢 {context.get('company') or 'Не указана'}\n"
        f"📞 {context.get('phone') or 'Не указан'}\n"
        f"🎫 ITSM логин: {context.get('itsm') or 'Нет'}\n"
        f"📝 Проблема: {context.get('problem') or 'Не указана'}\n"
        f"🆔 ID Удаленного доступа: {context.get('anydesk') or 'Нет'}\n"
        f"💻 {context.get('pc_name') or 'N/A'}\n"
        f"Локальный IP: {context.get('local_ip') or 'N/A'} | Внешний IP: {context.get('ext_ip') or 'N/A'}\n"
        f"MAC: {context.get('mac_addr') or 'N/A'}\n"
        f"Domain: {context.get('domain_info') or 'N/A'}\n"
        f"GW: {context.get('gateway') or 'N/A'}\n"
        f"DC: {context.get('dc_name') or 'N/A'}\n\n"
        f"[ПИНГИ]\n"
        f"GW: {context.get('ping_gw') or 'N/A'} | DC: {context.get('ping_dc') or 'N/A'}\n"
        f"8.8.8.8: {context.get('ping_8888') or 'N/A'} | 1.1.1.1: {context.get('ping_1111') or 'N/A'}\n"
        f"NSLookup ya.ru: {context.get('nslookup_res') or 'N/A'}"
        f"{traces_section}\n"
        f"--- ОСНОВНОЙ TRACE WAN (MTR YA.RU) ---\n"
        f"{normalize_output(str(context.get('trace_res') or ''))}\n"
    )
    return report.strip() + "\n"
