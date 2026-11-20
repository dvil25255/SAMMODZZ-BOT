import os
from dotenv import load_dotenv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')

@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    admin_id: int = int(os.getenv("ADMIN_ID", "0") or 0)
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    max_file_bytes: int = int(os.getenv("MAX_FILE_BYTES", str(20 * 1024 * 1024)))
    backup_retention_days: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    storage_dir: Path = Path(os.getenv("STORAGE_DIR", str(ROOT / "storage"))).expanduser()
    @property
    def scripts_dir(self): return self.storage_dir / "scripts"
    @property
    def offsets_dir(self): return self.storage_dir / "offsets"
    @property
    def backups_dir(self): return self.storage_dir / "backups"
    @property
    def logs_dir(self): return self.storage_dir / "logs"

settings = Settings()
for directory in (settings.scripts_dir, settings.offsets_dir, settings.backups_dir, settings.logs_dir):
    directory.mkdir(parents=True, exist_ok=True)
