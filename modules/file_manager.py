import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from modules.security import clean_filename

class FileManager:
    def __init__(self, settings, db):
        self.settings, self.db = settings, db

    def _target_dir(self, name):
        return self.settings.scripts_dir if Path(name).suffix.lower() == ".lua" else self.settings.offsets_dir

    def store_upload(self, original_name, payload, actor_id):
        safe_name = clean_filename(original_name)
        if not payload:
            raise ValueError("Empty file.")
        if len(payload) > self.settings.max_file_bytes:
            raise ValueError("File exceeds configured size limit.")
        file_id = uuid.uuid4().hex
        suffix = Path(safe_name).suffix.lower()
        stored_name = file_id + suffix
        target = self._target_dir(safe_name) / stored_name
        target.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        record = {
            "id": file_id, "original_name": safe_name, "stored_name": stored_name,
            "storage_type": "scripts" if suffix == ".lua" else "offsets",
            "size_bytes": len(payload), "sha256": digest, "uploaded_by": int(actor_id),
        }
        try:
            self.db.add_file(record)
            self.db.log_event(actor_id, "upload", safe_name)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return record

    def resolve_file(self, file_id):
        item = self.db.get_file(file_id)
        if not item:
            return None, None
        folder = self.settings.scripts_dir if item["storage_type"] == "scripts" else self.settings.offsets_dir
        path = (folder / item["stored_name"]).resolve()
        if folder.resolve() not in path.parents or not path.is_file():
            return None, item
        return path, item

    def delete_file(self, file_id):
        path, item = self.resolve_file(file_id)
        if not item:
            return False
        if path and path.exists():
            path.unlink()
        self.db.delete_file_record(file_id)
        self.db.log_event(self.settings.admin_id, "delete", item["original_name"])
        return True

    def backup_file(self, path):
        if not path.is_file():
            raise FileNotFoundError(path)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_name = f"{path.stem}_{stamp}{path.suffix}.bak"
        destination = self.settings.backups_dir / backup_name
        destination.write_bytes(path.read_bytes())
        return destination

    def cleanup_backups(self):
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.settings.backup_retention_days)
        removed = 0
        for path in self.settings.backups_dir.glob("*.bak"):
            modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            if modified < cutoff:
                path.unlink(missing_ok=True)
                removed += 1
        self.db.log_event(self.settings.admin_id, "backup_cleanup", f"Removed {removed}")
        return removed
