import shutil
import platform
import os

def system_report(settings):
    usage = shutil.disk_usage(settings.storage_dir)
    total = usage.total / (1024 ** 3)
    free = usage.free / (1024 ** 3)
    return (
        "<b>System health</b>\n"
        f"Platform: <code>{platform.system()} {platform.release()}</code>\n"
        f"Python: <code>{platform.python_version()}</code>\n"
        f"Storage free: <code>{free:.2f} GB</code> / {total:.2f} GB\n"
        f"PID: <code>{os.getpid()}</code>\n"
        f"Max upload: <code>{settings.max_file_bytes // (1024*1024)} MB</code>"
    )
