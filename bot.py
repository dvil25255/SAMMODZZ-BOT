import telebot
from telebot import types
import os, json, shutil, random, string, re
from datetime import datetime, timedelta
from supabase import create_client, Client

# ============================================================
# SAMMODZZ ULTIMATE BOT v16.0 (Real Bypass Injector + Auth)
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not BOT_TOKEN or not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Environment Variables! Please set BOT_TOKEN, SUPABASE_URL, and SUPABASE_KEY in Railway.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE = "./SAMMODZZ/"
SCRIPTS = BASE + "scripts/"
OFFSETS = BASE + "offsets/"
BACKUPS = BASE + "backups/"
LOGS = BASE + "logs/"
BYPASS_DIR = BASE + "bypass/"
FUTURE_PLANS_FILE = BASE + "future_plans.json"

for d in [SCRIPTS, OFFSETS, BACKUPS, LOGS, BYPASS_DIR]:
    os.makedirs(d, exist_ok=True)

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

def is_admin(msg): return msg.from_user.id == ADMIN_ID

# ============================================================
# SUPABASE STORAGE FUNCTIONS
# ============================================================
def upload_to_supabase(file_path, file_name):
    try:
        with open(file_path, 'rb') as f:
            supabase.storage.from_('scripts').upload(file_name, f, {'upsert': 'true'})
        return True
    except Exception as e:
        print(f'Upload error: {e}')
        return False

def download_from_supabase(file_name, local_path):
    try:
        data = supabase.storage.from_('scripts').download(file_name)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f'Download error: {e}')
        return False

# ============================================================
# SAFE BYPASS INJECTOR
# ============================================================
def get_bypass_code():
    bypass_file = BYPASS_DIR + "master_bypass.lua"
    download_from_supabase("master_bypass.lua", bypass_file)
    if os.path.exists(bypass_file):
        with open(bypass_file, "r", encoding="utf-8") as f:
            return f.read()
    return "-- No custom bypass provided\n"

def inject_safe_bypass(content):
    bypass_code = get_bypass_code()
    safe_wrapper = f"""
-- ============================================================
-- SAMMODZZ SAFE BYPASS SYSTEM
-- ============================================================
local _bypass_success, _bypass_err = pcall(function()
{bypass_code}
end)
if not _bypass_success then
    print("[SAMMODZZ] Bypass warning: " .. tostring(_bypass_err))
end
-- ============================================================
"""
    return safe_wrapper + "\n" + content

# ============================================================
# INJECT AUTH + OFFSETS + BRANDING
# ============================================================
def inject_auth_and_offsets(content, branding, version):
    offsets_table = {}
    try:
        res = supabase.table('offsets').select('*').eq('game_version', version).execute()
        for row in (res.data or []):
            offsets_table[row['offset_name']] = row['offset_value']
    except Exception as e:
        print(f"Offset fetch error: {e}")

    offsets_lua = ",\n".join([f'    ["{k}"] = {v}' for k, v in offsets_table.items()])

    auth_code = f"""
-- ============================================================
-- {branding} — Game Version: {version}
-- ============================================================
_G.SAMMODZZ_AUTO_AUTH = true
_G._LICENSE_OK = false
_G._SAMMODZZ_LICENSE_OK = false
_G.BRANDING = "{branding}"
_G.GAME_VERSION = "{version}"

_G._OFFSETS = {{
{offsets_lua}
}}
"""
    content = content.replace('@Masterpiece2025', branding).replace('MASTERAHSANYT', branding)
    return auth_code + "\n" + content, len(offsets_table)

# ============================================================
# OBFUSCATION
# ============================================================
def real_obfuscate(content):
    mapping = {}
    def rname(name):
        if name in ["self", "true", "false", "nil", "end", "and", "or", "not", "function", "return", "if", "then", "else", "elseif", "for", "while", "do", "in", "local", "break"]: return name
        if name not in mapping: mapping[name] = "v_" + ''.join(random.choices(string.ascii_lowercase, k=6))
        return mapping[name]

    content = re.sub(r'\blocal\s+function\s+([a-zA-Z_]\w*)', lambda m: 'local function ' + rname(m.group(1)), content)
    content = re.sub(r'\blocal\s+([a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)*)', lambda m: 'local ' + ', '.join(rname(v.strip()) for v in m.group(1).split(',')), content)

    junk = "\n"
    for _ in range(8):
        n = "junk_" + ''.join(random.choices(string.ascii_lowercase, k=8))
        a = random.randint(100, 999)
        junk += f"local function {n}() local x = {a} + {a} if x > 50000 then return true end return false end\n"

    return content + junk

# ============================================================
# BYPASS TOGGLE SETTING
# ============================================================
@bot.message_handler(commands=['setbypass'])
def toggle_bypass(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ Aap admin nahi hain!")
        return
    user_id = message.from_user.id
    if user_id not in user_states:
        user_states[user_id] = {}
    current = user_states[user_id].get('use_bypass', True)
    user_states[user_id]['use_bypass'] = not current
    status = "✅ ON (Bypass lagayega)" if user_states[user_id]['use_bypass'] else "❌ OFF (Bypass nahi lagayega)"
    bot.reply_to(message, f"🔄 Bypass status ab: {status}\n\nAb jo bhi file aap bhejoge, usme bypass {'lagaya jayega' if user_states[user_id]['use_bypass'] else 'nahi lagaya jayega'}.")

# ============================================================
# WIZARD: File Upload Flow
# ============================================================
@bot.message_handler(content_types=['document'])
def handle_doc(msg):
    if not is_admin(msg): return
    try:
        file_info = bot.get_file(msg.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        filename = msg.document.file_name

        if filename.endswith(".lua"):
            if "bypass" in filename.lower():
                dest = BYPASS_DIR + "master_bypass.lua"
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as f: f.write(downloaded)
                upload_to_supabase(dest, "master_bypass.lua")
                return bot.reply_to(msg, "✅ <b>Master Bypass Saved!</b>\nAb har script is safe bypass ke saath build hogi.", parse_mode="HTML")

            dest = SCRIPTS + "TEMP_" + filename
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f: f.write(downloaded)
            upload_to_supabase(dest, "TEMP_" + filename)
            
            if user_states.get(msg.from_user.id, {}).get('use_bypass', True):
                with open(dest, "r", encoding="utf-8") as f: content = f.read()
                content = inject_safe_bypass(content)
                with open(dest, "w", encoding="utf-8") as f: f.write(content)

            user_states[msg.chat.id] = {"filepath": dest, "filename": filename}
            markup = types.InlineKeyboardMarkup(row_width=3)
            markup.add(
                types.InlineKeyboardButton("1 Day", callback_data="exp_1d"),
                types.InlineKeyboardButton("30 Days", callback_data="exp_30d"),
                types.InlineKeyboardButton("1 Year", callback_data="exp_1y"),
                types.InlineKeyboardButton("Lifetime", callback_data="exp_life")
            )
            bot.reply_to(msg, "📜 <b>Script Received!</b>\n\n1️⃣ <b>License Key kitne din ki banani hai?</b>", parse_mode="HTML", reply_markup=markup)

        elif filename.endswith(".txt"):
            dest = OFFSETS + filename
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f: f.write(downloaded)
            upload_to_supabase(dest, filename)
            bot.reply_to(msg, f"🎯 <b>Offsets Uploaded:</b> {filename}", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(msg, f"❌ Error: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("exp_"))
def cb_expiry(call):
    bot.answer_callback_query(call.id)
    process_expiry(call.message, call.data.split("_")[1])

def process_expiry(msg, expiry):
    chat_id = msg.chat.id
    if chat_id not in user_states: return
    user_states[chat_id]["expiry"] = expiry
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🔨 Build Now", callback_data="build"))
    bot.send_message(chat_id, "✅ Expiry set! Ab build par click karein.", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "build")
def cb_build(call):
    bot.answer_callback_query(call.id)
    try:
        # Supabase se files list karo
        files = supabase.storage.from_("scripts").list()
        scripts = [f["name"] for f in files if f["name"].endswith(".lua") and not f["name"].startswith("TEMP_") and f["name"] != "master_bypass.lua"]
        if not scripts: return bot.send_message(call.message.chat.id, "❌ No scripts found in Supabase.")
        markup = types.InlineKeyboardMarkup(row_width=1)
        for s in scripts:
            markup.add(types.InlineKeyboardButton(s, callback_data=f"build_sel:{s}"))
        bot.send_message(call.message.chat.id, "🔨 <b>Select Script:</b>", parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Supabase Error: {e}")
@bot.callback_query_handler(func=lambda c: c.data.startswith("build_sel:"))
def cb_build_sel(call):
    bot.answer_callback_query(call.id)
    script = call.data.split(":")[1]
    bot.send_message(call.message.chat.id, f"✅ Selected: {script}")

@bot.message_handler(commands=['start'])
def start(msg):
    if not is_admin(msg): return
    markup = types.InlineKeyboardMarkup(row_width=2)
    text = (
        "```\n╔══════════════════════════╗\n║ SAMMODZZ ULTIMATE v16.0  ║\n╚══════════════════════════╝\n```\n"
        f"🟢 ONLINE | 💾 Scripts: <code>{len(os.listdir(SCRIPTS))}</code>\n\n"
        "🔽 <b>Tools:</b>\n"
        "<i>Koi bhi .lua bhejo — Bot puchega details aur secure build karke dega.</i>\n"
        "<i>Bypass file (bypass.lua) bhejo — Bot har script me use lagayega.</i>"
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=markup)

if __name__ == "__main__":
    print("Bot starting...")
    bot.infinity_polling()
# Updated Build Logic
