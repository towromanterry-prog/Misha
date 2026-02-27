import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

APP_NAME = "AURORA.GERMES"
REPORTS_SUBDIR = "reports"
USER_PROFILE_FILENAME = "user_profile.json"
MAX_REPORT_FILES = 20


def get_app_data_dir(app_name: str) -> str:
    """Возвращает каталог для данных приложения."""
    if os.name == "nt":
        base_dir = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA")
        if base_dir:
            app_dir = Path(base_dir) / app_name
            app_dir.mkdir(parents=True, exist_ok=True)
            return str(app_dir)

    # Fallback для не-Windows окружений и экзотических случаев.
    app_dir = Path.home() / ".local" / "share" / app_name
    app_dir.mkdir(parents=True, exist_ok=True)
    return str(app_dir)


def _sanitize_filename_part(value: str, default: str = "report") -> str:
    safe = "".join(c for c in value if c.isalnum() or c in " -_").strip()
    return safe or default


def _cleanup_old_reports(reports_dir: Path, max_files: int = MAX_REPORT_FILES) -> None:
    report_files = sorted(
        [p for p in reports_dir.glob("*.txt") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old_file in report_files[max_files:]:
        try:
            old_file.unlink(missing_ok=True)
        except Exception:
            continue


def save_text_report(text: str, filename_prefix: str) -> Tuple[str, str]:
    app_dir = Path(get_app_data_dir(APP_NAME))
    reports_dir = app_dir / REPORTS_SUBDIR
    reports_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_prefix = _sanitize_filename_part(filename_prefix, default="Диагностика")
    filename = f"{safe_prefix}_{date_str}.txt"
    file_path = reports_dir / filename

    file_path.write_text(text, encoding="utf-8")
    _cleanup_old_reports(reports_dir)
    return str(file_path), filename


def save_user_profile(data: Dict[str, Any]) -> str:
    app_dir = Path(get_app_data_dir(APP_NAME))
    profile_path = app_dir / USER_PROFILE_FILENAME
    profile_path.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
    return str(profile_path)


def load_user_profile() -> Dict[str, Any]:
    app_dir = Path(get_app_data_dir(APP_NAME))
    profile_path = app_dir / USER_PROFILE_FILENAME
    if not profile_path.exists():
        return {}

    try:
        return json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def clear_user_profile() -> None:
    app_dir = Path(get_app_data_dir(APP_NAME))
    profile_path = app_dir / USER_PROFILE_FILENAME
    try:
        profile_path.unlink(missing_ok=True)
    except Exception:
        pass
