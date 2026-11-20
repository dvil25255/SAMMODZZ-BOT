import logging
import os
import threading
from pathlib import Path

import telebot
from telebot import types
from dotenv import load_dotenv

from config import settings
from modules.database import Database
from modules.file_manager import FileManager
from modules.security import is_admin, safe_callback_id
from modules.license_manager import LicenseManager
from modules.system_monitor import system_report
from modules.statistics import format_stats

load_dotenv()
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.logs_dir / "bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("sammodzz")

if not settings.bot_token or settings.bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
    raise SystemExit("Set BOT_TOKEN in .env before starting.")
if not settings.admin_id:
    raise SystemExit("Set ADMIN_ID in .env before starting.")

db = Database(settings)
fm = FileManager(settings, db)
licenses = LicenseManager(db)
bot = telebot.TeleBot(settings.bot_token, parse_mode="HTML", threaded=True)

def admin_message(fn):
    def wrapped(message, *args, **kwargs):
        if not is_admin(message.from_user.id, settings.admin_id):
            bot.reply_to(message, "⛔ Access denied.")
            return
        return fn(message, *args, **kwargs)
    wrapped.__name__ = fn.__name__
    return wrapped

def admin_callback(fn):
    def wrapped(call, *args, **kwargs):
        if not is_admin(call.from_user.id, settings.admin_id):
            bot.answer_callback_query(call.id, "Access denied", show_alert=True)
            return
        return fn(call, *args, **kwargs)
    wrapped.__name__ = fn.__name__
    return wrapped

def main_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("📁 Files", callback_data="menu:files"),
        types.InlineKeyboardButton("📤 Upload help", callback_data="menu:upload"),
        types.InlineKeyboardButton("📊 Statistics", callback_data="menu:stats"),
        types.InlineKeyboardButton("🖥 System health", callback_data="menu:health"),
        types.InlineKeyboardButton("🔑 Generate license", callback_data="menu:key"),
        types.InlineKeyboardButton("🧹 Cleanup backups", callback_data="menu:cleanup"),
    )
    return m

@bot.message_handler(commands=["start", "help"])
@admin_message
def start(message):
    bot.send_message(
        message.chat.id,
        "<b>SAMMODZZ V13 ULTIMATE</b>\n"
        "Secure file management and automation bot.\n\n"
        "Send a .lua or .txt document to store it safely.\n"
        "Use the menu below or /commands for commands.",
        reply_markup=main_menu(),
    )

@bot.message_handler(commands=["commands"])
@admin_message
def commands(message):
    bot.reply_to(
        message,
        "<b>Commands</b>\n"
        "/start - Main menu\n/files - Browse stored files\n/stats - File and activity statistics\n"
        "/health - Runtime and storage health\n/genkey - Generate an app license key\n"
        "/cleanup - Remove old backup copies\n"
        "/commands - Show this list\n\n"
        "Upload .lua or .txt files as Telegram documents."
    )

@bot.message_handler(commands=["files"])
@admin_message
def files_command(message):
    send_file_list(message.chat.id)

def send_file_list(chat_id):
    records = db.list_files(limit=30)
    if not records:
        bot.send_message(chat_id, "No files stored yet.")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for item in records:
        name = item.get("original_name", "unnamed")
        fid = safe_callback_id(item.get("id", ""))
        if not fid:
            continue
        markup.add(types.InlineKeyboardButton(f"📄 {name[: forty()]}", callback_data=f"file:{fid}"))
    bot.send_message(chat_id, "<b>Stored files</b> (latest 30)", reply_markup=markup)

def forty():
    return 40

@bot.message_handler(commands=["stats"])
@admin_message
def stats_command(message):
    bot.reply_to(message, format_stats(db))

@bot.message_handler(commands=["health"])
@admin_message
def health_command(message):
    bot.reply_to(message, system_report(settings))

@bot.message_handler(commands=["genkey"])
@admin_message
def genkey_command(message):
    key = licenses.generate()
    bot.reply_to(message, f"🔑 New license key:\n<code>{key}</code>\n\nStore it securely.")

@bot.message_handler(commands=["cleanup"])
@admin_message
def cleanup_command(message):
    removed = fm.cleanup_backups()
    bot.reply_to(message, f"🧹 Removed {removed} expired backup file(s).")

@bot.message_handler(content_types=["document"])
@admin_message
def handle_document(message):
    doc = message.document
    try:
        if doc.file_size and doc.file_size > settings.max_file_bytes:
            bot.reply_to(message, f"File too large. Limit: {settings.max_file_bytes // (1024*1024)} MB.")
            return
        info = bot.get_file(doc.file_id)
        payload = bot.download_file(info.file_path)
        record = fm.store_upload(doc.file_name or "upload.bin", payload, message.from_user.id)
        bot.reply_to(
            message,
            "✅ <b>File stored safely</b>\n"
            f"Name: <code>{record['original_name']}</code>\n"
            f"Size: {record['size_bytes']} bytes\n"
            f"SHA-256: <code>{record['sha256'][:20]}...</code>\n"
            "Use Files to retrieve it."
        )
    except Exception as exc:
        log.exception("Upload failed")
        bot.reply_to(message, f"❌ Upload failed: {str(exc)[:250]}")

@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    if not is_admin(call.from_user.id, settings.admin_id):
        bot.answer_callback_query(call.id, "Access denied", show_alert=True)
        return
    data = call.data or ""
    try:
        if data == "menu:files":
            bot.answer_callback_query(call.id)
            send_file_list(call.message.chat.id)
        elif data == "menu:upload":
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "Send a Telegram document ending in .lua or .txt. Maximum size is configured in .env.")
        elif data == "menu:stats":
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, format_stats(db))
        elif data == "menu:health":
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, system_report(settings))
        elif data == "menu:key":
            bot.answer_callback_query(call.id)
            key = licenses.generate()
            bot.send_message(call.message.chat.id, f"🔑 <code>{key}</code>")
        elif data == "menu:cleanup":
            bot.answer_callback_query(call.id)
            removed = fm.cleanup_backups()
            bot.send_message(call.message.chat.id, f"Cleanup complete. Removed {removed} backup(s).")
        elif data.startswith("file:"):
            bot.answer_callback_query(call.id)
            fid = safe_callback_id(data.split(":", 1)[1])
            item = db.get_file(fid) if fid else None
            if not item:
                bot.send_message(call.message.chat.id, "File record not found.")
                return
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("📥 Download", callback_data=f"dl:{fid}"),
                types.InlineKeyboardButton("💾 Backup", callback_data=f"backup:{fid}"),
                types.InlineKeyboardButton("🗑 Delete", callback_data=f"del:{fid}"),
            )
            markup.add(types.InlineKeyboardButton("🔙 Files", callback_data="menu:files"))
            bot.send_message(
                call.message.chat.id,
                f"<b>{item['original_name']}</b>\n"
                f"Size: {item['size_bytes']} bytes\n"
                f"SHA-256: <code>{item['sha256']}</code>\n"
                f"Uploaded: {item.get('created_at', 'unknown')}",
                reply_markup=markup,
            )
        elif data.startswith("dl:"):
            bot.answer_callback_query(call.id)
            fid = safe_callback_id(data.split(":", 1)[1])
            path, item = fm.resolve_file(fid)
            if not path or not item:
                bot.send_message(call.message.chat.id, "File not found on disk.")
                return
            with path.open("rb") as stream:
                bot.send_document(call.message.chat.id, stream, visible_file_name=item["original_name"])
            db.log_event(settings.admin_id, "download", item["original_name"])
        elif data.startswith("backup:"):
            bot.answer_callback_query(call.id)
            fid = safe_callback_id(data.split(":", 1)[1])
            path, item = fm.resolve_file(fid) if fid else (None, None)
            if not path or not item:
                bot.send_message(call.message.chat.id, "File not found on disk.")
                return
            backup_path = fm.backup_file(path)
            db.log_event(settings.admin_id, "backup", item["original_name"])
            with backup_path.open("rb") as stream:
                bot.send_document(call.message.chat.id, stream, caption=f"💾 Backup: {item['original_name']}")
        elif data.startswith("del:"):
            bot.answer_callback_query(call.id, "Deleting…")
            fid = safe_callback_id(data.split(":", 1)[1])
            ok = fm.delete_file(fid)
            bot.send_message(call.message.chat.id, "🗑 File deleted." if ok else "Could not delete file.")
        else:
            bot.answer_callback_query(call.id, "Unknown action")
    except Exception:
        log.exception("Callback failed: %s", data)
        bot.answer_callback_query(call.id, "Action failed", show_alert=True)

def run():
    log.info("SAMMODZZ V13 starting")
    db.log_event(settings.admin_id, "startup", "Bot started")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
        except Exception:
            log.exception("Polling stopped; retrying in 5 seconds")
            threading.Event().wait(5)

if __name__ == "__main__":
    run()
