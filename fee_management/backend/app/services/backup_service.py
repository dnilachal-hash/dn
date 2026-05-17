"""Database backup and restore service (SQLite-focused)."""
import shutil
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from app.config import settings

BACKUP_DIR = Path("./data/backups")


def _ensure_backup_dir():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _get_db_path() -> Optional[Path]:
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///./"):
        return Path(url[len("sqlite:///./"):])
    if url.startswith("sqlite:///"):
        return Path(url[len("sqlite:///"):])
    return None


def create_backup(db=None) -> Dict:
    """Copy SQLite DB file to backups/ folder with timestamp filename."""
    _ensure_backup_dir()
    db_path = _get_db_path()
    if not db_path or not db_path.exists():
        raise ValueError("SQLite database file not found or not SQLite URL. Backup only supported for SQLite.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"fee_management_backup_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_filename

    shutil.copy2(db_path, backup_path)

    size = backup_path.stat().st_size
    return {
        "filename": backup_filename,
        "path": str(backup_path),
        "size": size,
        "size_human": _human_size(size),
        "created_at": datetime.now().isoformat(),
    }


def list_backups() -> List[Dict]:
    """List all backup files sorted by newest first."""
    _ensure_backup_dir()
    backups = []
    for f in sorted(BACKUP_DIR.glob("*.db"), key=lambda x: x.stat().st_mtime, reverse=True):
        stat = f.stat()
        backups.append({
            "filename": f.name,
            "size": stat.st_size,
            "size_human": _human_size(stat.st_size),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return backups


def restore_backup(backup_filename: str, db=None) -> Dict:
    """
    Copy backup file over the active database.
    WARNING: This replaces the live database. The app should be restarted after.
    """
    _ensure_backup_dir()
    backup_path = BACKUP_DIR / backup_filename
    if not backup_path.exists():
        raise ValueError(f"Backup file '{backup_filename}' not found.")

    db_path = _get_db_path()
    if not db_path:
        raise ValueError("Only SQLite restore is supported.")

    # Close any sessions and copy
    if db:
        try:
            db.close()
        except Exception:
            pass

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pre_restore_backup = BACKUP_DIR / f"pre_restore_{timestamp}.db"
    if db_path.exists():
        shutil.copy2(db_path, pre_restore_backup)

    shutil.copy2(backup_path, db_path)
    return {
        "restored_from": backup_filename,
        "pre_restore_backup": pre_restore_backup.name,
        "restored_at": datetime.now().isoformat(),
        "message": "Restore complete. Please restart the server to reload the database.",
    }


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
