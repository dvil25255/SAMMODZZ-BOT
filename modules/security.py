import re
from pathlib import PurePath

ALLOWED_EXTENSIONS = {".lua", ".txt"}

def is_admin(user_id, admin_id):
    return bool(user_id and admin_id and int(user_id) == int(admin_id))

def clean_filename(name):
    # Keep only the final path component; reject control characters and unsafe names.
    name = str(name or "").replace("\\", "/").split("/")[-1].strip()
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name)
    name = name.lstrip(".").strip()
    if not name or name in {".", ".."}:
        raise ValueError("Invalid filename.")
    if len(name) > 120:
        stem, suffix = PurePath(name).stem, PurePath(name).suffix
        name = stem[: max(1, 120 - len(suffix))] + suffix[:20]
    ext = PurePath(name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Only .lua and .txt files are allowed.")
    return name

def safe_callback_id(value):
    value = str(value or "")
    return value if re.fullmatch(r"[a-f0-9]{32}", value) else None
