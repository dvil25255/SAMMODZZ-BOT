
def detect_features(content):
    features = []
    text = content.lower()
    if "aimbot" in text or "aim " in text or "aim/" in text: features.append("Aimbot")
    if "esp" in text or "wallhack" in text or "chams" in text: features.append("ESP / Wallhack")
    if "skin" in text or "outfit" in text: features.append("Skins")
    if "car" in text or "vehicle" in text: features.append("Vehicle Hacks")
    if "memory" in text or "grass" in text or "fog" in text: features.append("Memory / Environment")
    if "fakehwid" in text or "hwid" in text: features.append("Fake HWID")
    if "ipad" in text or "fov" in text: features.append("iPad / FOV")
    if not features: features.append("Basic Script")
    return features

def get_key_system():
    # Supabase wala code (jo pehle banaya tha)
    return '''
-- SUPABASE ONLINE KEY SYSTEM
_G.LunarLoginRuntime = _G.LunarLoginRuntime or {}
_G.LunarLoginRuntime.Authorized = false
_G.LunarLoginRuntime.Status = "Enter Key"
function _G.MasterLicenseLogin(entered_key)
    local http = nil
    pcall(function() local MM = require("client.module_framework.ModuleManager"); http = MM.GetModule(MM.CommonModuleConfig.http_manager) end)
    if not http then _G.LunarLoginRuntime.Status = "HTTP not found"; return false end
    local url = os.getenv("SUPABASE_URL") .. "/rest/v1/keys?key=eq." .. entered_key .. "&select=*"
    http:Get(url, {["apikey"] = os.getenv("SUPABASE_KEY"), ["Authorization"] = "Bearer " .. os.getenv("SUPABASE_KEY")}, function(success, response)
        if success and response then
            local json = require("common.json_util"); local data = json.decode(response)
            if data and #data > 0 then
                local row = data[1]
                if row.is_used == false or row.is_used == nil then
                    _G.LunarLoginRuntime.Authorized = true
                    _G.LunarLoginRuntime.Status = "Login Success!"
                else _G.LunarLoginRuntime.Status = "Key already used!" end
            else _G.LunarLoginRuntime.Status = "Invalid Key!" end
        else _G.LunarLoginRuntime.Status = "Connection failed" end
    end, 10)
end
function _G.MasterLicenseLogout() _G.LunarLoginRuntime.Authorized = false end
'''

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
            
            with open(dest, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            features = detect_features(content)
            user_states[msg.chat.id] = {
                "filepath": dest, "filename": filename, "features": features, "selected": {f: True for f in features}
            }
            show_feature_menu(msg.chat.id)

        elif filename.endswith(".txt"):
            dest = OFFSETS + filename
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f: f.write(downloaded)
            bot.reply_to(msg, "🎯 <b>Offsets Uploaded:</b> " + filename, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(msg, "❌ Error: " + str(e))

def show_feature_menu(chat_id):
    state = user_states.get(chat_id)
    if not state: return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for feat, is_on in state['selected'].items():
        icon = "✅" if is_on else "❌"
        markup.add(types.InlineKeyboardButton(f"{icon} {feat}", callback_data=f"toggle_{feat}"))
    markup.add(types.InlineKeyboardButton("🚀 Build & Inject Key System", callback_data="build_final"))
    bot.send_message(chat_id, "🔍 <b>Features Detected!</b>\n\nChunein ki kya chahiye (ON) aur kya nahi (OFF):", parse_mode="HTML", reply_markup=markup)

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
    markup.add(types.InlineKeyboardButton("🚀 Build & Inject Key System", callback_data="build_final"))
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "build_final")
def cb_build_final(call):
    chat_id = call.message.chat.id
    if chat_id not in user_states: return
    bot.answer_callback_query(call.id)
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="⏳ File process ho rahi hai...")
    
    state = user_states[chat_id]
    try:
        with open(state['filepath'], 'r', encoding='utf-8') as f:
            content = f.read()
            
        config_code = "-- ==========================================\n-- USER CONFIGURATION\n-- ==========================================\n"
        config_code += "_G.SZ = _G.SZ or {}\n_G.SZ.Aimbot = _G.SZ.Aimbot or {}\n"
        config_code += f"_G.SZ.Aimbot.Enable = {'true' if state['selected'].get('Aimbot', False) else 'false'}\n"
        config_code += "_G.SZ.ESP = _G.SZ.ESP or {}\n"
        config_code += f"_G.SZ.ESP.Master = {'true' if state['selected'].get('ESP / Wallhack', False) else 'false'}\n"
        
        key_system = get_key_system()
        new_content = config_code + "\n\n" + key_system + "\n\n" + content
        
        final_path = SCRIPTS + "Final_" + state['filename']
        with open(final_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        with open(final_path, 'rb') as f:
            bot.send_document(chat_id, f, caption="✅ <b>Build Complete!</b>\nFeatures Applied & Supabase Key System Injected.", parse_mode="HTML")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}")
    del user_states[chat_id]


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


def get_key_system():
    return '''
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
    
    if not http then 
        _G.LunarLoginRuntime.Status = "HTTP Module not found"
        return false 
    end
    
    _G.LunarLoginRuntime.Status = "Checking key..."
    local url = "YOUR_SUPABASE_URL/rest/v1/keys?key=eq." .. entered_key .. "&select=*"
    
    http:Get(url, {
        ["apikey"] = "YOUR_SUPABASE_KEY",
        ["Authorization"] = "Bearer YOUR_SUPABASE_KEY"
    }, function(success, response)
        if success and response then
            local json = require("common.json_util")
            local data = json.decode(response)
            if data and #data > 0 then
                local row = data[1]
                if row.is_used == false or row.is_used == nil then
                    _G.LunarLoginRuntime.Authorized = true
                    _G.LunarLoginRuntime.Status = "Login Success! Welcome VIP."
                    
                    local patch_url = "YOUR_SUPABASE_URL/rest/v1/keys?key=eq." .. entered_key
                    http:Patch(patch_url, {
                        ["apikey"] = "YOUR_SUPABASE_KEY",
                        ["Authorization"] = "Bearer YOUR_SUPABASE_KEY",
                        ["Content-Type"] = "application/json",
                        ["Prefer"] = "return=minimal"
                    }, '{"is_used": true}', function(p_success, p_resp) end, 10)
                    
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
'''
