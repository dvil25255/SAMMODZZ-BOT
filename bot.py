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

for d in [SCRIPTS, OFFSETS, BACKUPS, LOGS, BYPASS_DIR]:
    os.makedirs(d, exist_ok=True)

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

def is_admin(msg): return msg.from_user.id == ADMIN_ID

# ============================================================
# SAFE BYPASS INJECTOR
# ============================================================
def get_bypass_code():
    bypass_file = BYPASS_DIR + "master_bypass.lua"
    if os.path.exists(bypass_file):
        with open(bypass_file, "r", encoding="utf-8") as f:
            return f.read()
    return "-- No custom bypass provided" + chr(10)

def inject_safe_bypass(content):
    bypass_code = get_bypass_code()
    safe_wrapper = "-- ============================================================" + chr(10)
    safe_wrapper += "-- SAMMODZZ SAFE BYPASS SYSTEM" + chr(10)
    safe_wrapper += "-- ============================================================" + chr(10)
    safe_wrapper += "local _bypass_success, _bypass_err = pcall(function()" + chr(10)
    safe_wrapper += bypass_code + chr(10)
    safe_wrapper += "end)" + chr(10)
    safe_wrapper += "if not _bypass_success then" + chr(10)
    safe_wrapper += '    print("[SAMMODZZ] Bypass warning: " .. tostring(_bypass_err))' + chr(10)
    safe_wrapper += "end" + chr(10)
    safe_wrapper += "-- ============================================================" + chr(10)
    return safe_wrapper + chr(10) + content

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
        print("Offset fetch error: " + str(e))

    offsets_lua = ",\n".join(['    ["' + k + '"] = ' + v for k, v in offsets_table.items()])

    auth_code = "-- ============================================================" + chr(10)
    auth_code += "-- " + branding + " — Game Version: " + version + chr(10)
    auth_code += "-- ============================================================" + chr(10)
    auth_code += "_G.SAMMODZZ_AUTO_AUTH = true" + chr(10)
    auth_code += "_G._LICENSE_OK = false" + chr(10)
    auth_code += "_G._SAMMODZZ_LICENSE_OK = false" + chr(10)
    auth_code += '_G.BRANDING = "' + branding + '"' + chr(10)
    auth_code += '_G.GAME_VERSION = "' + version + '"' + chr(10)
    auth_code += chr(10)
    auth_code += "_G._OFFSETS = {" + chr(10)
    auth_code += offsets_lua + chr(10)
    auth_code += "}" + chr(10)

    content = content.replace('@Masterpiece2025', branding).replace('MASTERAHSANYT', branding)
    return auth_code + chr(10) + content, len(offsets_table)

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

    junk = chr(10)
    for _ in range(8):
        n = "junk_" + ''.join(random.choices(string.ascii_lowercase, k=8))
        a = random.randint(100, 999)
        junk += "local function " + n + "() local x = " + str(a) + " + " + str(a) + " if x > 50000 then return true end return false end" + chr(10)

    return content + junk

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
                return bot.reply_to(msg, "✅ Master Bypass Saved!")

            dest = SCRIPTS + filename
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f: f.write(downloaded)
            
            user_states[msg.chat.id] = {"filepath": dest, "filename": filename, "step": 1}
            markup = types.ForceReply(selective=True)
            
            step1_msg = "📜 <b>Script Received:</b> " + filename + chr(10) + chr(10) + "<b>Step 1/7:</b> Apni <b>Branding Name</b> likhein (jaise: Masterpiece):"
            bot.reply_to(msg, step1_msg, parse_mode="HTML", reply_markup=markup)

        elif filename.endswith(".txt"):
            dest = OFFSETS + filename
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f: f.write(downloaded)
            bot.reply_to(msg, "🎯 <b>Offsets Uploaded:</b> " + filename, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(msg, "❌ Error: " + str(e))


@bot.message_handler(func=lambda msg: msg.chat.id in user_states and "step" in user_states[msg.chat.id])
def wizard_steps(msg):
    chat_id = msg.chat.id
    state = user_states[chat_id]
    step = state.get("step")
    text = msg.text

    if step == 1:
        state["branding"] = text
        state["step"] = 2
        bot.reply_to(msg, "<b>Step 2/7:</b> Game ka <b>Version</b> likhein (jaise: 3.2.0):", parse_mode="HTML", reply_markup=types.ForceReply(selective=True))

    elif step == 2:
        state["version"] = text
        state["step"] = 3
        bot.reply_to(msg, "<b>Step 3/7:</b> Kya aap <b>License Key System</b> add karna chahte hain? (Haan/Nahi):", parse_mode="HTML", reply_markup=types.ForceReply(selective=True))

    elif step == 3:
        state["key_system"] = (text.lower() == "haan" or text.lower() == "yes")
        state["step"] = 4
        bot.reply_to(msg, "<b>Step 4/7:</b> Kya aap <b>Config (Settings)</b> system add karna chahte hain? (Haan/Nahi):", parse_mode="HTML", reply_markup=types.ForceReply(selective=True))

    elif step == 4:
        state["config_system"] = (text.lower() == "haan" or text.lower() == "yes")
        state["step"] = 5
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Haan", callback_data="wiz_bypass_yes"), types.InlineKeyboardButton("❌ Nahi", callback_data="wiz_bypass_no"))
        bot.reply_to(msg, "<b>Step 5/7:</b> Kya aap is script me <b>Bypass</b> lagana chahte hain?", parse_mode="HTML", reply_markup=markup)

    elif step == 5:
        bot.reply_to(msg, "Kripya Haan ya Nahi button par click karein.")

    elif step == 6:
        state["custom_text"] = text if text.lower() != 'none' else None
        state["step"] = 7
        bot.reply_to(msg, "<b>Step 7/7:</b> Kya aap koi <b>Fake Date/Time</b> set karna chahte hain? (Format: YYYY-MM-DD HH:MM:SS ya 'None' likhein):", parse_mode="HTML", reply_markup=types.ForceReply(selective=True))

    elif step == 7:
        state["fake_time"] = text if text.lower() != 'none' else None
        bot.reply_to(msg, "⏳ <b>Aapki saari details mil gayi hain. File build ho rahi hai...</b>", parse_mode="HTML")
        
        try:
            filepath = state["filepath"]
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if state.get("use_bypass", True):
                content = inject_safe_bypass(content)
            
            content, offset_count = inject_auth_and_offsets(content, state["branding"], state["version"])
            
            if state.get("key_system"):
                license_code = "-- LICENSE KEY SYSTEM (Auto-Injected)" + chr(10)
                license_code += "_G.License = { Key = 'MODDED-KEY-123', Expiry = '2026-12-31', Verified = false }" + chr(10)
                license_code += "function _G.CheckLicense(key)" + chr(10)
                license_code += "    if key == _G.License.Key then" + chr(10)
                license_code += "        _G.License.Verified = true" + chr(10)
                license_code += "        return true" + chr(10)
                license_code += "    end" + chr(10)
                license_code += "    return false" + chr(10)
                license_code += "end" + chr(10)
                content = license_code + content

            if state.get("config_system"):
                config_code = "-- CONFIG SYSTEM (Auto-Injected)" + chr(10)
                config_code += "_G.Config = { ESP = true, Aimbot = false, Wallhack = true, Speed = 1.0, Distance = 500 }" + chr(10)
                content = config_code + content

            if state.get("custom_text"):
                content = "-- " + state["custom_text"] + chr(10) + content
                
            if state.get("fake_time"):
                time_code = "-- FAKE TIME INJECTED" + chr(10) + "_G.FakeTime = '" + state["fake_time"] + "'" + chr(10)
                content = time_code + content

            content = real_obfuscate(content)
            final_name = "Modded_" + state["filename"]
            final_path = SCRIPTS + final_name
            with open(final_path, "w", encoding="utf-8") as f:
                f.write(content)

            with open(final_path, "rb") as f:
                cap = "✅ <b>Build Complete!</b>" + chr(10) + chr(10)
                cap += "🏷 Branding: " + state["branding"] + chr(10)
                cap += "🎮 Version: " + state["version"] + chr(10)
                cap += "🔑 Key System: " + ('ON' if state.get('key_system') else 'OFF') + chr(10)
                cap += "⚙ Config: " + ('ON' if state.get('config_system') else 'OFF') + chr(10)
                cap += "🔒 Bypass: " + ('ON' if state.get('use_bypass', True) else 'OFF')
                bot.send_document(chat_id, f, caption=cap, parse_mode="HTML")

        except Exception as e:
            bot.send_message(chat_id, "❌ Error: " + str(e))
        
        del user_states[chat_id]


@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_bypass_"))
def cb_wizard_bypass(call):
    chat_id = call.message.chat.id
    if chat_id not in user_states: return
    
    if call.data == "wiz_bypass_yes":
        user_states[chat_id]["use_bypass"] = True
    else:
        user_states[chat_id]["use_bypass"] = False

    user_states[chat_id]["step"] = 6
    bot.send_message(chat_id, "<b>Step 6/7:</b> Kya aap koi <b>Special Text/Developer Name</b> add karna chahte hain? (Agar nahi, toh 'None' likhein):", parse_mode="HTML", reply_markup=types.ForceReply(selective=True))
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)

@bot.message_handler(commands=['setbypass'])
def toggle_bypass(message):
    if not is_admin(message): return
    user_id = message.from_user.id
    if user_id not in user_states: user_states[user_id] = {}
    current = user_states[user_id].get('use_bypass', True)
    user_states[user_id]['use_bypass'] = not current
    status = "✅ ON" if user_states[user_id]['use_bypass'] else "❌ OFF"
    bot.reply_to(message, "🔄 Bypass status: " + status)

@bot.message_handler(commands=['start'])
def start(msg):
    if not is_admin(msg): return
    bot.send_message(msg.chat.id, "✅ Bot is Online. Send a .lua file to start.")

if __name__ == "__main__":
    print("Bot starting...")
    bot.infinity_polling()
