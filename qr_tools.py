"""Offline-утилиты для подготовки QR с mailto-ссылкой."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from PIL import Image


def extract_tracert_hops(output: str, max_hops: int = 5) -> str:
    """Возвращает строки хопов tracert (1..max_hops) без заголовка."""
    normalized = (output or "").replace("\r\n", "\n").replace("\r", "\n")
    hop_lines: list[str] = []

    for raw_line in normalized.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split()
        if not parts or not parts[0].isdigit():
            continue

        hop_number = int(parts[0])
        if 1 <= hop_number <= max_hops:
            hop_lines.append(line)

    return "\n".join(hop_lines)


def build_mailto(to: str, subject: str, body: str) -> str:
    """Собирает mailto-ссылку с url-encode для subject/body."""
    safe_to = (to or "").strip()
    encoded_subject = quote(subject or "", safe="")
    encoded_body = quote(body or "", safe="")
    return f"mailto:{safe_to}?subject={encoded_subject}&body={encoded_body}"


def generate_qr_image(text: str) -> "Image.Image":
    """Генерирует QR-код из произвольного текста."""
    try:
        import qrcode
    except ImportError as exc:
        raise RuntimeError("Для генерации QR требуется пакет 'qrcode'.") from exc

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(text or "")
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")
