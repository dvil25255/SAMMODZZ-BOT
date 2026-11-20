import telebot
from telebot import types
import os, json, shutil, random, string, re, traceback
from datetime import datetime, timedelta
from supabase import create_client, Client

# ============================================================
# CONFIGURATION
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not BOT_TOKEN or not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Env Vars! Please set BOT_TOKEN, SUPABASE_URL, and SUPABASE_KEY.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Paths
BASE = "./SAMMODZZ/"
SCRIPTS = BASE + "scripts/"
OFFSETS = BASE + "offsets/"
BYPASS_DIR = BASE + "bypass/"
for d in [SCRIPTS, OFFSETS, BYPASS_DIR]:
    os.makedirs(d, exist_ok=True)

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

def is_admin(msg): return msg.from_user.id == ADMIN_ID

# ============================================================
# SUPABASE FUNCTIONS
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
    except Exception:
        return False

def get_bypass_code():
    bypass_file = BYPASS_DIR + "master_bypass.lua"
    download_from_supabase("master_bypass.lua", bypass_file)
    if os.path.exists(bypass_file):
        with open(bypass_file, "r", encoding="utf-8") as f:
            return f.read()
    return "-- No custom bypass provided\n"

# ============================================================
# LUA INJECTORS
# ============================================================
def inject_safe_bypass(content):
    bypass_code = get_bypass_code()
    safe_wrapper = "-- ============================================================\n"
    safe_wrapper += "-- SAMMODZZ SAFE BYPASS SYSTEM\n"
    safe_wrapper += "-- ============================================================\n"
    safe_wrapper += "local _bypass_success, _bypass_err = pcall(function()\n"
    safe_wrapper += bypass_code + "\n"
    safe_wrapper += "end)\n"
    safe_wrapper += "if not _bypass_success then\n"
    safe_wrapper += '    print("[SAMMODZZ] Bypass warning: " .. tostring(_bypass_err))\n'
    safe_wrapper += "end\n"
    safe_wrapper += "-- ============================================================\n"
    return safe_wrapper + "\n" + content

def detect_features(content):
    features = []
    text = content.lower()
    if "aimbot" in text or "aim " in text: features.append("Aimbot")
    if "esp" in text or "wallhack" in text or "chams" in text: features.append("ESP / Wallhack")
    if "skin" in text or "outfit" in text: features.append("Skins")
    if "car" in text or "vehicle" in text: features.append("Vehicle Hacks")
    if "memory" in text or "grass" in text or "fog" in text: features.append("Memory / Environment")
    if "fakehwid" in text or "hwid" in text: features.append("Fake HWID")
    if "ipad" in text or "fov" in text: features.append("iPad / FOV")
    if not features: features.append("Basic Script")
    return features

def get_key_system():
    lua = """
-- ============================================================
-- SUPABASE ONLINE KEY SYSTEM (Auto-Injected)
-- ============================================================
_G.LunarLoginRuntime = _G.LunarLoginRuntime or {}
_G.LunarLoginRuntime.Authorized = false
_G.LunarLoginRuntime.Status = "Enter Key"

function _G.MasterLicenseLogin(entered_key)
    local http = nil
    pcall(function()
        local MM = require("client.module_framework.ModuleManager")
        http = MM.GetModule(MM.CommonModuleConfig.http_manager)
    end)
    if not http then _G.LunarLoginRuntime.Status = "HTTP Module not found"; return false end
    
    _G.LunarLoginRuntime.Status = "Checking key..."
    local url = "SUPABASE_URL_PLACEHOLDER/rest/v1/keys?key=eq." .. entered_key .. "&select=*"
    local headers = {
        ["apikey"] = "SUPABASE_KEY_PLACEHOLDER",
        ["Authorization"] = "Bearer SUPABASE_KEY_PLACEHOLDER"
    }
    
    http:Get(url, headers, function(success, response)
        if success and response then
            local json = require("common.json_util")
            local data = json.decode(response)
            if data and #data > 0 then
                local row = data[1]
                if row.is_used == false or row.is_used == nil then
                    _G.LunarLoginRuntime.Authorized = true
                    _G.LunarLoginRuntime.Status = "Login Success! Welcome VIP."
                    
                    local patch_url = "SUPABASE_URL_PLACEHOLDER/rest/v1/keys?key=eq." .. entered_key
                    http:Patch(patch_url, headers, '{"is_used": true}', function(p_success, p_resp) end, 10)
                else
                    _G.LunarLoginRuntime.Status = "Key already used!"
                end
            else
                _G.LunarLoginRuntime.Status = "Invalid Key!"
            end
        else
            _G.LunarLoginRuntime.Status = "Connection failed"
        end
    end, 10)
end

function _G.MasterLicenseLogout()
    _G.LunarLoginRuntime.Authorized = false
    _G.LunarLoginRuntime.Status = "Logged out"
end
"""
    lua = lua.replace("SUPABASE_URL_PLACEHOLDER", SUPABASE_URL)
    lua = lua.replace("SUPABASE_KEY_PLACEHOLDER", SUPABASE_KEY)
    return lua

# ============================================================
# ADMIN PANEL (FULLY WORKING)
# ============================================================
@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if not is_admin(msg): return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔑 Generate Key", callback_data="admin_gen"),
        types.InlineKeyboardButton("🔄 Renew Key", callback_data="admin_renew")
    )
    markup.add(
        types.InlineKeyboardButton("🛡️ Update Bypass", callback_data="admin_bypass"),
        types.InlineKeyboardButton("🎯 Update Offsets", callback_data="admin_offset")
    )
    markup.add(types.InlineKeyboardButton("📊 System Stats", callback_data="admin_stats"))
    
    ui_text = (
        "👑 <b>ADMIN CONTROL PANEL</b> 👑\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Yahan se aap apne bot ko manage kar sakte hain.\n\n"
        "🔽 <i>Neeche diye gaye options me se chunein:</i>"
    )
    bot.send_message(msg.chat.id, ui_text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def handle_admin_callbacks(call):
    if not is_admin(call.message): return
    bot.answer_callback_query(call.id)
    action = call.data.split("_")[1]

    if action == "gen":
        try:
            new_key = f"SAMMODZZ-VIP-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
            res = supabase.table('keys').insert({"key": new_key, "is_used": False}).execute()
            if res.data:
                bot.send_message(call.message.chat.id, f"✅ <b>Key Generated Successfully!</b>\n\n🔑 Key: <code>{new_key}</code>", parse_mode="HTML")
            else:
                bot.send_message(call.message.chat.id, "❌ Key insert failed. Supabase me 'keys' table check karein.")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Supabase Error: {e}\n\nMake sure 'keys' table has columns: 'key' (text) and 'is_used' (bool).")

    elif action == "renew":
        msg = bot.send_message(call.message.chat.id, "🔄 Kripya <b>Key</b> bhejein jo renew karni hai:")
        bot.register_next_step_handler(msg, process_renew_key)

    elif action == "bypass":
        msg = bot.send_message(call.message.chat.id, "🛡️ Kripya nayi <b>Bypass (.lua)</b> file bhejein:")
        bot.register_next_step_handler(msg, process_update_bypass)

    elif action == "offset":
        msg = bot.send_message(call.message.chat.id, "🎯 Kripya nayi <b>Offsets (.txt)</b> file bhejein:")
        bot.register_next_step_handler(msg, process_update_offset)

    elif action == "stats":
        try:
            res = supabase.table('keys').select('*').execute()
            total = len(res.data)
            used = len([k for k in res.data if k.get('is_used')])
            unused = total - used
            stats_text = f"📊 <b>SYSTEM STATISTICS</b>\n━━━━━━━━━━━━━━━━━━━━\n📦 <b>Total Keys:</b> {total}\n✅ <b>Used:</b> {used}\n💎 <b>Available:</b> {unused}"
            bot.send_message(call.message.chat.id, stats_text, parse_mode="HTML")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Error: {e}")

def process_renew_key(message):
    if not message.text:
        return bot.reply_to(message, "❌ Kripya sirf text (key) bhejein, file nahi.")
    key = message.text.strip()
    try:
        res = supabase.table('keys').update({"is_used": False}).eq("key", key).execute()
        if res.data:
            bot.reply_to(message, f"✅ Key <code>{key}</code> successfully renew ho gayi! Ab yeh use ho sakti hai.", parse_mode="HTML")
        else:
            bot.reply_to(message, "❌ Key nahi mili database me. Spelling check karein.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

def process_update_bypass(message):
    if not message.document:
        return bot.reply_to(message, "❌ Aapne file nahi bheji! Admin panel se dubara try karein.")
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        with open(BYPASS_DIR + "master_bypass.lua", "wb") as f: f.write(downloaded)
        upload_to_supabase(BYPASS_DIR + "master_bypass.lua", "master_bypass.lua")
        bot.reply_to(message, "✅ <b>Bypass successfully update ho gaya!</b>\nAb har nayi file is bypass ke sath banegi.", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

def process_update_offset(message):
    if not message.document:
        return bot.reply_to(message, "❌ Aapne file nahi bheji! Admin panel se dubara try karein.")
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        filename = message.document.file_name
        with open(OFFSETS + filename, "wb") as f: f.write(downloaded)
        upload_to_supabase(OFFSETS + filename, filename)
        bot.reply_to(message, f"✅ <b>Offsets ({filename}) successfully update ho gaye!</b>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# ============================================================
# WIZARD FLOW & BUILD
# ============================================================
@bot.message_handler(commands=['start'])
def start(msg):
    if not is_admin(msg): return
    ui_text = (
        "🌟 <b>SAMMODZZ CYBER BOT v16.0</b> 🌟\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 <b>Status:</b> Online\n"
        "⚡ <b>Engine:</b> Supabase + Lua\n\n"
        "📥 <b>Kaise use karein?</b>\n"
        "👉 Koi bhi <code>.lua</code> file bhejein.\n"
        "👉 Bot aapse details puchega.\n"
        "👉 Select karein aur Build dabayein!\n\n"
        "🛠️ <i>Admin Panel ke liye /admin likhein.</i>"
    )
    bot.send_message(msg.chat.id, ui_text, parse_mode="HTML")

@bot.message_handler(content_types=['document'])
def handle_doc(msg):
    if not is_admin(msg): return
    try:
        file_info = bot.get_file(msg.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        filename = msg.document.file_name

        if filename.endswith(".lua"):
            dest = SCRIPTS + filename
            with open(dest, "wb") as f: f.write(downloaded)
            
            with open(dest, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            features = detect_features(content)
            user_states[msg.chat.id] = {
                "filepath": dest, "filename": filename, "features": features, "selected": {f: True for f in features}, "step": "ask_branding"
            }
            
            bot.reply_to(msg, "📜 <b>Script Received:</b> " + filename + "\n\n<b>Step 1/4:</b> Apni <b>Branding Name</b> likhein (jaise: Masterpiece):", parse_mode="HTML", reply_markup=types.ForceReply(selective=True))
    except Exception as e:
        bot.reply_to(msg, "❌ Error: " + str(e))

@bot.message_handler(func=lambda msg: msg.chat.id in user_states and "step" in user_states[msg.chat.id])
def wizard_steps(msg):
    chat_id = msg.chat.id
    state = user_states[chat_id]
    step = state.get("step")
    text = msg.text if msg.text else "None"

    if step == "ask_branding":
        state["branding"] = text
        state["step"] = "ask_version"
        bot.reply_to(msg, "<b>Step 2/4:</b> Game ka <b>Version</b> likhein (jaise: 4.6):", parse_mode="HTML", reply_markup=types.ForceReply(selective=True))

    elif step == "ask_version":
        state["version"] = text
        state["step"] = "ask_bypass"
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✅ Haan", callback_data="wiz_bypass_yes"), types.InlineKeyboardButton("❌ Nahi", callback_data="wiz_bypass_no"))
        bot.reply_to(msg, "<b>Step 3/4:</b> Kya aap is script me <b>Bypass</b> lagana chahte hain?", parse_mode="HTML", reply_markup=markup)

    elif step == "ask_keysystem":
        state["use_keysystem"] = (text.lower() == "haan" or text.lower() == "yes")
        state["step"] = "feature_menu"
        show_feature_menu(chat_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("wiz_bypass_"))
def cb_wizard_bypass(call):
    chat_id = call.message.chat.id
    if chat_id not in user_states: return
    
    state = user_states[chat_id]
    state["use_bypass"] = (call.data == "wiz_bypass_yes")
    state["step"] = "ask_keysystem"
    
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    bot.send_message(chat_id, "<b>Step 4/4:</b> Kya aap <b>Key System</b> add karna chahte hain? (Haan/Nahi):", parse_mode="HTML", reply_markup=types.ForceReply(selective=True))

def show_feature_menu(chat_id):
    state = user_states.get(chat_id)
    if not state: return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for feat, is_on in state['selected'].items():
        icon = "✅" if is_on else "❌"
        markup.add(types.InlineKeyboardButton(f"{icon} {feat}", callback_data=f"toggle_{feat}"))
    markup.add(types.InlineKeyboardButton("🚀 Build File", callback_data="build_final"))
    
    ui_text = (
        "🔍 <b>FEATURE DETECTOR</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📁 <b>File:</b> <code>{state['filename']}</code>\n\n"
        "✅ = ON | ❌ = OFF\n\n"
        "👇 <i>Toggle karne ke liye click karein:</i>"
    )
    bot.send_message(chat_id, ui_text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def cb_toggle(call):
    chat_id = call.message.chat.id
    if chat_id not in user_states: return
    feat = call.data.replace("toggle_", "")
    user_states[chat_id]['selected'][feat] = not user_states[chat_id]['selected'][feat]
    bot.answer_callback_query(call.id)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for f, is_on in user_states[chat_id]['selected'].items():
        icon = "✅" if is_on else "❌"
        markup.add(types.InlineKeyboardButton(f"{icon} {f}", callback_data=f"toggle_{f}"))
    markup.add(types.InlineKeyboardButton("🚀 Build File", callback_data="build_final"))
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "build_final")
def cb_build_final(call):
    chat_id = call.message.chat.id
    if chat_id not in user_states: return
    bot.answer_callback_query(call.id)
    
    building_text = "⚙️ <b>BUILDING FILE...</b>\n━━━━━━━━━━━━━━━━━━━━\n🔄 Bypass inject ho raha hai...\n🔑 Key System add ho raha hai...\n⚡ Features apply ho rahe hain..."
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=building_text, parse_mode="HTML")
    
    state = user_states[chat_id]
    try:
        with open(state['filepath'], 'r', encoding='utf-8') as f:
            content = f.read()
            
        if state.get("use_bypass", True):
            content = inject_safe_bypass(content)
            
        config_code = "-- ==========================================\n"
        config_code += "-- USER FEATURE CONFIGURATION\n"
        config_code += "-- ==========================================\n"
        config_code += "_G.SZ = _G.SZ or {}\n"
        config_code += "_G.SZ.Aimbot = _G.SZ.Aimbot or {}\n"
        config_code += f"_G.SZ.Aimbot.Enable = {'true' if state['selected'].get('Aimbot', False) else 'false'}\n"
        config_code += "_G.SZ.ESP = _G.SZ.ESP or {}\n"
        config_code += f"_G.SZ.ESP.Master = {'true' if state['selected'].get('ESP / Wallhack', False) else 'false'}\n"
        
        if state.get("use_keysystem", True):
            key_system = get_key_system()
            content = config_code + "\n\n" + key_system + "\n\n" + content
        else:
            content = config_code + "\n\n" + content
            
        header = f"-- ==========================================\n-- BRANDING: {state.get('branding', 'Unknown')}\n-- VERSION: {state.get('version', 'Unknown')}\n-- ==========================================\n"
        content = header + content
        
        final_path = SCRIPTS + "Final_" + state['filename']
        with open(final_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        with open(final_path, 'rb') as f:
            caption = (
                "✅ <b>BUILD COMPLETE!</b> ✅\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 <b>File:</b> <code>Final_{state['filename']}</code>\n"
                f"🏷 <b>Branding:</b> {state.get('branding')}\n"
                f"🎮 <b>Version:</b> {state.get('version')}\n"
                f"🛡️ <b>Bypass:</b> {'ON' if state.get('use_bypass') else 'OFF'}\n"
                f"🔑 <b>Key System:</b> {'ON' if state.get('use_keysystem') else 'OFF'}\n\n"
                "🚀 <i>Script ready to use!</i>"
            )
            bot.send_document(chat_id, f, caption=caption, parse_mode="HTML")
            
        upload_to_supabase(final_path, "Final_" + state['filename'])
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}")
        
    del user_states[chat_id]

if __name__ == "__main__":
    print("Bot starting with Premium UI & Working Admin Panel...")
    bot.infinity_polling()
