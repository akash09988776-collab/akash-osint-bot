import json
import os
import re
import sys
import requests
import threading
from datetime import datetime
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ---------- ENVIRONMENT VARIABLES ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8827201871:AAH_dWGvDD1KvxCCdy30sm0cz_6VZ-zTuhM")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "8979291976,8333711029").split(",")]

# ---------- CHANNELS (4 TOTAL) ----------
CHANNELS = [
    {"name": "Channel 1", "username": "@wftis_ak4sh", "link": "https://t.me/wftis_ak4sh"},
    {"name": "Channel 2", "username": "@Err9r403", "link": "https://t.me/Err9r403"},
    {"name": "Channel 3", "username": "@AkashOSINT", "link": "https://t.me/AkashOSINT"},
    {"name": "Group GC", "username": "+EfWs0w63dYgwNTg1", "link": "https://t.me/+EfWs0w63dYgwNTg1"}
]

# ---------- API URLs ----------
API_NUMBER = "https://darkxapi.onrender.com/api/v1/info?key=Dark&query={}"
API_IFSC = "https://vercei-kappa.vercel.app/ifsc?code={}"
API_PINCODE = "https://nitin-apis-update-birthday-spacial.vercel.app/api?type=pincode&search={}"
API_WEATHER = "https://nitin-wather-check-api.vercel.app/api?type=weather&search={}"
API_EMAIL = "https://travelers-creature-sarah-rogers.trycloudflare.com/search?q={}"
API_AADHAR = "https://darkxapi.onrender.com/api/v1/info?key=Dark&query={}"
API_IP = "https://talks-chain-restrictions-statistics.trycloudflare.com/search?query={}"
API_PAN = "https://counted-developing-parade-man.trycloudflare.com/pan-info?pan={}"
API_TG_TO_NUM = "https://tg2num-botadminshere.vercel.app/?id={}"   # NEW

COINS_ON_START = 5
COST_PER_LOOKUP = 1
REFERRAL_BONUS = 1
HISTORY_LIMIT = 10
DATA_FILE = "user_data.json"
BLOCK_FILE = "blocked_users.json"
QUERY_LOG_FILE = "query_log.json"
MAX_LOG_ENTRIES = 200

# ---------- DATA HANDLING ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_blocked():
    if os.path.exists(BLOCK_FILE):
        with open(BLOCK_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_blocked(blocked_set):
    with open(BLOCK_FILE, "w") as f:
        json.dump(list(blocked_set), f)

def load_query_log():
    if os.path.exists(QUERY_LOG_FILE):
        with open(QUERY_LOG_FILE, "r") as f:
            return json.load(f)
    return []

def save_query_log(log):
    with open(QUERY_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def get_user_data(user_id, name=None):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "coins": COINS_ON_START,
            "referrals": 0,
            "referred_by": None,
            "history": [],
            "name": name,
            "phone": None
        }
        save_data(data)
    elif name and not data[uid].get("name"):
        data[uid]["name"] = name
        save_data(data)
    return data[uid]

def update_user_data(user_id, new_data):
    data = load_data()
    data[str(user_id)] = new_data
    save_data(data)

# ---------- CONTINUOUS VERIFICATION ----------
async def is_member(user_id, context):
    for ch in CHANNELS:
        try:
            if ch["username"].startswith("+"):
                continue
            member = await context.bot.get_chat_member(chat_id=ch["username"], user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

async def is_verified(user_id, context):
    if user_id in ADMIN_IDS:
        return True
    if user_id in load_blocked():
        return False
    return await is_member(user_id, context)

# ---------- KEYBOARDS ----------
def get_user_keyboard():
    buttons = [
        ["📱 𝘕𝘶𝘮𝘣𝘦𝘳 𝘓𝘰𝘰𝘬𝘶𝘱", "🪪 𝘈𝘥𝘩𝘢𝘢𝘳 𝘓𝘰𝘰𝘬𝘶𝘱"],
        ["💳 𝘗𝘢𝘯 𝘓𝘰𝘰𝘬𝘶𝘱", "🏦 𝘐𝘍𝘚𝘊 𝘓𝘰𝘰𝘬𝘶𝘱"],
        ["📍 𝘗𝘪𝘯 𝘊𝘰𝘥𝘦", "🌐 𝘐𝘗 𝘓𝘰𝘰𝘬𝘶𝘱"],
        ["📧 𝘌𝘮𝘢𝘪𝘭 𝘓𝘰𝘰𝘬𝘶𝘱", "☁️ 𝘞𝘦𝘢𝘵𝘩𝘦𝘳 𝘓𝘰𝘰𝘬𝘶𝘱"],
        ["🔢 𝘛𝘎 𝘵𝘰 𝘕𝘶𝘮", "👤 𝘔𝘺 𝘈𝘤𝘤𝘰𝘶𝘯𝘵"],
        ["🔗 𝘙𝘦𝘧𝘦𝘳𝘳𝘢𝘭"]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)

def get_admin_keyboard():
    buttons = [
        ["📱 𝘕𝘶𝘮𝘣𝘦𝘳 𝘓𝘰𝘰𝘬𝘶𝘱", "🪪 𝘈𝘥𝘩𝘢𝘢𝘳 𝘓𝘰𝘰𝘬𝘶𝘱"],
        ["💳 𝘗𝘢𝘯 𝘓𝘰𝘰𝘬𝘶𝘱", "🏦 𝘐𝘍𝘚𝘊 𝘓𝘰𝘰𝘬𝘶𝘱"],
        ["📍 𝘗𝘪𝘯 𝘊𝘰𝘥𝘦", "🌐 𝘐𝘗 𝘓𝘰𝘰𝘬𝘶𝘱"],
        ["📧 𝘌𝘮𝘢𝘪𝘭 𝘓𝘰𝘰𝘬𝘶𝘱", "☁️ 𝘞𝘦𝘢𝘵𝘩𝘦𝘳 𝘓𝘰𝘰𝘬𝘶𝘱"],
        ["🔢 𝘛𝘎 𝘵𝘰 𝘕𝘶𝘮", "👤 𝘔𝘺 𝘈𝘤𝘤𝘰𝘶𝘯𝘵"],
        ["🛠️ 𝘉𝘰𝘵 𝘔𝘢𝘯𝘢𝘨𝘦𝘮𝘦𝘯𝘵"]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)

def get_bot_management_menu():
    keyboard = [
        [InlineKeyboardButton("🎁 Give Coin", callback_data="admin_givecoin")],
        [InlineKeyboardButton("🎁 Give All Users Coin", callback_data="admin_giveallcoins")],
        [InlineKeyboardButton("🤖 Bot Messenger", callback_data="admin_bot_messenger")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("📊 QueryScope", callback_data="admin_query_scope")],
        [InlineKeyboardButton("🚫 Block User", callback_data="admin_block")],
        [InlineKeyboardButton("✅ Unblock User", callback_data="admin_unblock")],
        [InlineKeyboardButton("👥 All Users", callback_data="admin_all_users")],
        [InlineKeyboardButton("🚫 Blocked Users", callback_data="admin_blocked_users")],
        [InlineKeyboardButton("❌ Close", callback_data="admin_close")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]
    return InlineKeyboardMarkup(keyboard)

def get_bot_messenger_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 Text Message", callback_data="msg_text")],
        [InlineKeyboardButton("🖼️ Photo", callback_data="msg_photo")],
        [InlineKeyboardButton("🎥 Video", callback_data="msg_video")],
        [InlineKeyboardButton("🎵 Audio/Song", callback_data="msg_audio")],
        [InlineKeyboardButton("📄 Document", callback_data="msg_document")],
        [InlineKeyboardButton("🎞️ GIF", callback_data="msg_gif")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_keyboard(user_id=None):
    if user_id and user_id in ADMIN_IDS:
        return get_admin_keyboard()
    return get_user_keyboard()

# ---------- FORMAT FUNCTIONS (ALL FIXED) ----------

def format_number_output(data):
    if not data:
        return "❌ No data found."
    
    results = []
    query = None
    
    if isinstance(data, dict):
        query = data.get("query") or data.get("q") or data.get("number")
        
        if "results" in data:
            results = data["results"]
        elif "data" in data and isinstance(data["data"], dict) and "results" in data["data"]:
            results = data["data"]["results"]
        elif "data" in data and isinstance(data["data"], list):
            results = data["data"]
    
    if not results:
        q = query or "Unknown"
        return f"❌ No data found for number: `{q}`\n\n💡 Please check the number and try again."
    
    clean_results = []
    for record in results:
        clean_record = {}
        for key, value in record.items():
            if value is not None and value != "":
                clean_record[key] = value
        if clean_record:
            clean_results.append(clean_record)
    
    if not clean_results:
        q = query or "Unknown"
        return f"❌ No data found for number: `{q}`"
    
    clean_data = {
        "total_records": len(clean_results),
        "data": clean_results,
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    
    out = "**Number Lookup**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_aadhar_output(data):
    if not data:
        return "❌ No data found."
    
    results = []
    query = None
    
    if isinstance(data, dict):
        query = data.get("query") or data.get("q") or data.get("aadhar")
        
        if "results" in data:
            results = data["results"]
        elif "data" in data and isinstance(data["data"], dict) and "results" in data["data"]:
            results = data["data"]["results"]
        elif "data" in data and isinstance(data["data"], list):
            results = data["data"]
    
    if not results:
        q = query or "Unknown"
        return f"❌ No data found for Aadhar: `{q}`\n\n💡 Please check the number and try again (12 digits)."
    
    clean_results = []
    for record in results:
        clean_record = {}
        for key, value in record.items():
            if value is not None and value != "":
                clean_record[key] = value
        if clean_record:
            clean_results.append(clean_record)
    
    if not clean_results:
        q = query or "Unknown"
        return f"❌ No data found for Aadhar: `{q}`"
    
    clean_data = {
        "total_records": len(clean_results),
        "data": clean_results,
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    
    out = "**Aadhar Info**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_pan_output(data):
    if not data:
        return "❌ No data found."
    
    results = []
    query = None
    
    if isinstance(data, dict):
        query = data.get("query") or data.get("q") or data.get("pan")
        
        if "results" in data:
            results = data["results"]
        elif "data" in data and isinstance(data["data"], dict) and "results" in data["data"]:
            results = data["data"]["results"]
        elif "data" in data and isinstance(data["data"], list):
            results = data["data"]
        elif "data" in data and isinstance(data["data"], dict):
            results = [data["data"]]
    
    if not results:
        if isinstance(data, dict) and "pan" in data:
            results = [data]
        else:
            q = query or "Unknown"
            return f"❌ No data found for PAN: `{q}`\n\n💡 Please check the PAN number and try again."
    
    clean_results = []
    for record in results:
        if not isinstance(record, dict):
            continue
        clean = {}
        for key, value in record.items():
            if value is not None and value != "":
                clean[key] = value
        if clean:
            clean_results.append(clean)
    
    if not clean_results:
        q = query or "Unknown"
        return f"❌ No data found for PAN: `{q}`"
    
    result = {
        "total_records": len(clean_results),
        "data": clean_results,
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    out = "**PAN Info**\n```json\n"
    out += json.dumps(result, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_ifsc_output(data):
    if not data:
        return "❌ No data found."
    
    if "success" in data and data["success"] == False:
        return "❌ Invalid IFSC code or no data found."
    
    ifsc_data = data
    if "data" in data and isinstance(data["data"], dict):
        ifsc_data = data["data"]
    
    clean_data = {}
    for key, value in ifsc_data.items():
        if value is not None and value != "":
            clean_data[key] = value
    
    if not clean_data or len(clean_data) == 0:
        query = data.get("query") or data.get("code") or "Unknown"
        return f"❌ No data found for IFSC: `{query}`"
    
    clean_data["developer"] = "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    out = "**IFSC Lookup**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_pincode_output(data):
    if not data or data.get("status") != "success":
        return "❌ No data found for this PIN code."
    
    pincode = data.get("pincode", "N/A")
    status = data.get("status", "success")
    total_records = data.get("total_records_found") or data.get("total_records") or 1
    
    delivery_status = data.get("delivery_status")
    district = data.get("district")
    division = data.get("division")
    region = data.get("region")
    state = data.get("state")
    country = data.get("country")
    
    if not any([delivery_status, district, division, region, state, country]):
        records = data.get("records", [])
        if records and len(records) > 0:
            first = records[0]
            delivery_status = first.get("delivery_status", "N/A")
            district = first.get("district", "N/A")
            division = first.get("division", "N/A")
            region = first.get("region", "N/A")
            state = first.get("state", "N/A")
            country = first.get("country", "India")
    
    if not any([delivery_status, district, division, region, state, country]):
        return f"❌ No data found for PIN code: `{pincode}`"
    
    clean_data = {
        "status": status,
        "pincode": pincode,
        "total_records_found": total_records,
        "delivery_status": delivery_status or "N/A",
        "district": district or "N/A",
        "division": division or "N/A",
        "region": region or "N/A",
        "state": state or "N/A",
        "country": country or "India",
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    out = "**PIN Code Search**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_weather_output(data):
    if not data or not data.get("success") or not data.get("data"):
        return "❌ No weather data found for this location."
    
    w = data["data"]
    city = w.get("city", {})
    current = w.get("current", {})
    forecast = w.get("forecast", {}).get("daily_7day", [])
    
    if not city and not current:
        query = data.get("query") or "Unknown"
        return f"❌ No weather data found for: `{query}`"
    
    short_forecast = []
    for day in forecast[:3]:
        day_data = {}
        if day.get("date"): day_data["date"] = day.get("date")
        if day.get("temperature", {}).get("max_c"): day_data["max_c"] = day.get("temperature", {}).get("max_c")
        if day.get("temperature", {}).get("min_c"): day_data["min_c"] = day.get("temperature", {}).get("min_c")
        if day.get("precipitation", {}).get("total_mm"): day_data["rain_mm"] = day.get("precipitation", {}).get("total_mm")
        if day.get("weather", {}).get("icon"): day_data["icon"] = day.get("weather", {}).get("icon")
        if day_data:
            short_forecast.append(day_data)
    
    clean_data = {
        "city": city.get("searched"),
        "state": city.get("state"),
        "country": city.get("country"),
        "temperature": current.get("temperature", {}).get("actual_c"),
        "feels_like": current.get("temperature", {}).get("feels_like_c"),
        "humidity": current.get("atmosphere", {}).get("humidity_percent"),
        "wind": current.get("wind", {}).get("speed_kmh"),
        "forecast_3day": short_forecast,
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    
    out = "**Weather Check**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_email_output(data):
    if not data:
        return "❌ No data found."
    
    results = []
    query = None
    success = True
    
    if isinstance(data, dict):
        success = data.get("success", True)
        query = data.get("query") or data.get("q") or data.get("email")
        
        if "results" in data:
            results = data["results"]
        elif "data" in data and isinstance(data["data"], dict) and "results" in data["data"]:
            results = data["data"]["results"]
        elif "data" in data and isinstance(data["data"], list):
            results = data["data"]
    
    if not results:
        q = query or "Unknown"
        return f"❌ No data found for email: `{q}`\n\n💡 Please check the email address and try again."
    
    clean_data = {
        "success": success,
        "query": query or "N/A",
        "total_found": len(results),
        "results": results,
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    
    out = "**Email Info**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_ip_output(data):
    if not data:
        return "❌ No data found."
    
    ip_data = None
    
    if isinstance(data, dict):
        if 'data' in data and isinstance(data['data'], dict):
            ip_data = data['data']
        elif 'data' in data and isinstance(data['data'], list):
            ip_data = data['data']
        elif 'ip' in data:
            ip_data = data
        else:
            ip_data = data
    else:
        ip_data = data
    
    if ip_data is None:
        return "❌ No IP data found."
    
    if isinstance(ip_data, list):
        records = ip_data
    else:
        records = [ip_data]
    
    unwanted_keys = ['success', 'readme', 'developer']
    cleaned_records = []
    
    for rec in records:
        if not isinstance(rec, dict):
            cleaned_records.append(rec)
            continue
        clean = {}
        for key, value in rec.items():
            if key in unwanted_keys:
                continue
            if value is not None and value != "":
                clean[key] = value
        if clean:
            cleaned_records.append(clean)
    
    if not cleaned_records:
        query = data.get("query") or "Unknown"
        return f"❌ No data found for IP: `{query}`"
    
    result = {
        "total_records": len(cleaned_records),
        "data": cleaned_records,
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    out = "**IP Info**\n```json\n"
    out += json.dumps(result, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

# ---------- NEW: TG TO NUM FORMAT ----------
def format_tg_to_num_output(data):
    if not data:
        return "❌ No data found."
    
    # Check if API returned error
    if isinstance(data, dict) and data.get("success") == False:
        query = data.get("query") or "Unknown"
        return f"❌ No data found for Telegram ID: `{query}`"
    
    # Extract DATA field (if exists)
    if "𝘿𝘼𝙏𝘼" in data:
        data = data["𝘿𝘼𝙏𝘼"]
    
    success = data.get("𝙎𝙐𝘾𝘾𝙀𝙎𝙎", False)
    query = data.get("𝙌𝙐𝙀𝙍𝙔", "Unknown")
    result = data.get("𝙍𝙀𝙎𝙐𝙇𝙏", {})
    
    if not success:
        return f"❌ No data found for Telegram ID: `{query}`"
    
    phone = result.get("𝙋𝙃𝙊𝙉𝙀")
    country = result.get("𝘾𝙊𝙐𝙉𝙏𝙍𝙔")
    country_code = result.get("𝘾𝙊𝙐𝙉𝙏𝙍𝙔 𝘾𝙊𝘿𝙀")
    status = result.get("𝙇𝙊𝙊𝙆𝙐𝙋 𝙎𝙏𝘼𝙏𝙐𝙎", "UNKNOWN")
    
    if not phone:
        return f"❌ No data found for Telegram ID: `{query}`"
    
    clean_data = {
        "Telegram ID": query,
        "Phone": phone,
        "Country": country or "N/A",
        "Country Code": country_code or "N/A",
        "Status": status,
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    
    out = "**TG to Num Lookup**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

# ---------- QUERY LOGGING ----------
def log_query(user_id, name, query_type, query_input):
    log = load_query_log()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "name": name or "Unknown",
        "type": query_type,
        "query": query_input
    }
    log.append(entry)
    if len(log) > MAX_LOG_ENTRIES:
        log = log[-MAX_LOG_ENTRIES:]
    save_query_log(log)

# ---------- PERFORM LOOKUP ----------
async def perform_lookup(update, context, lookup_type, input_text):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    name = user_data.get("name", "Unknown")

    if user_id not in ADMIN_IDS:
        if user_data["coins"] < COST_PER_LOOKUP:
            await update.message.reply_text("❌ Not enough coins. Earn via referrals!")
            return
        user_data["coins"] -= COST_PER_LOOKUP

    if lookup_type == "number":
        url = API_NUMBER.format(input_text)
    elif lookup_type == "ifsc":
        url = API_IFSC.format(input_text)
    elif lookup_type == "pincode":
        url = API_PINCODE.format(input_text)
    elif lookup_type == "weather":
        url = API_WEATHER.format(input_text)
    elif lookup_type == "email":
        url = API_EMAIL.format(input_text)
    elif lookup_type == "aadhar":
        url = API_AADHAR.format(input_text)
    elif lookup_type == "ip":
        url = API_IP.format(input_text)
    elif lookup_type == "pan":
        url = API_PAN.format(input_text)
    elif lookup_type == "tg_to_num":
        url = API_TG_TO_NUM.format(input_text)
    else:
        await update.message.reply_text("Unknown lookup.")
        return

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"_raw": response.text}
    except Exception:
        await update.message.reply_text("❌ No results found or service unavailable. Please try again later.")
        return

    if lookup_type == "number":
        result = format_number_output(data)
    elif lookup_type == "ifsc":
        result = format_ifsc_output(data)
    elif lookup_type == "pincode":
        result = format_pincode_output(data)
    elif lookup_type == "weather":
        result = format_weather_output(data)
    elif lookup_type == "email":
        result = format_email_output(data)
    elif lookup_type == "aadhar":
        result = format_aadhar_output(data)
    elif lookup_type == "ip":
        result = format_ip_output(data)
    elif lookup_type == "pan":
        result = format_pan_output(data)
    elif lookup_type == "tg_to_num":
        result = format_tg_to_num_output(data)
    else:
        result = "Unknown"

    if len(user_data["history"]) >= HISTORY_LIMIT:
        user_data["history"].pop(0)
    user_data["history"].append(f"{lookup_type.upper()}: {input_text}")
    update_user_data(user_id, user_data)

    log_query(user_id, name, lookup_type, input_text)

    await update.message.reply_text(result, parse_mode="Markdown", reply_markup=get_keyboard(user_id))

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name or "User"

    get_user_data(user_id, first_name)

    ref = context.args[0] if context.args else None
    if ref and ref.isdigit() and int(ref) != user_id:
        data = load_data()
        uid = str(user_id)
        if uid not in data:
            data[uid] = {
                "coins": COINS_ON_START,
                "referrals": 0,
                "referred_by": int(ref),
                "history": [],
                "name": first_name,
                "phone": None
            }
            save_data(data)
            if str(ref) in data:
                data[str(ref)]["coins"] += REFERRAL_BONUS
                data[str(ref)]["referrals"] += 1
                save_data(data)

    if user_id in load_blocked():
        await update.message.reply_text("⛔ You are blocked from using this bot.")
        return

    if await is_verified(user_id, context):
        welcome = (
    f"ʜᴇʏ 👋 {first_name}\n\n"
    f"ʏᴏᴜʀ ɪᴅ ~ {user_id} ❤️\n\n"
    f"ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀᴋᴀsʜ ᴏsɪɴᴛ ʙᴏᴛ 🧑‍💻\n"
    f"ᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ."
)
        await update.message.reply_text(welcome, reply_markup=get_keyboard(user_id))
        return

    keyboard = []
    keyboard.append([InlineKeyboardButton("📢 𝘫𝘰𝘪𝘯 𝘤𝘩𝘢𝘯𝘯𝘦𝘭 𝟣", url=CHANNELS[0]["link"])])
    keyboard.append([InlineKeyboardButton("📢 𝘫𝘰𝘪𝘯 𝘤𝘩𝘢𝘯𝘯𝘦𝘭 𝟤", url=CHANNELS[1]["link"])])
    keyboard.append([InlineKeyboardButton("📢 𝘫𝘰𝘪𝘯 𝘤𝘩𝘢𝘯𝘯𝘦𝘭 𝟥", url=CHANNELS[2]["link"])])
    keyboard.append([InlineKeyboardButton("👥 𝘫𝘰𝘪𝘯 𝘨𝘳𝘰𝘶𝘱", url=CHANNELS[3]["link"])])
    keyboard.append([InlineKeyboardButton("✅ Verify", callback_data="verify")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Please join all channels & group to use this bot:\n\n"
        "After joining, press the Verify button.",
        reply_markup=reply_markup
    )

# ---------- RESTART COMMAND ----------
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        await update.message.reply_text("🔄 Bot is restarting...")
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        await update.message.reply_text("❌ You are not authorized to restart the bot.")

# ---------- SET PHONE COMMAND ----------
async def setphone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ Please send your phone number like:\n`/setphone +917250385668`", parse_mode="Markdown")
        return
    phone = " ".join(context.args).strip()
    if len(re.sub(r'\D', '', phone)) < 10:
        await update.message.reply_text("❌ Invalid phone number. Please include country code (e.g., +91...)")
        return
    data = load_data()
    uid = str(user_id)
    if uid in data:
        data[uid]["phone"] = phone
        save_data(data)
        await update.message.reply_text(f"✅ Your phone number has been set to: `{phone}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ You need to start the bot first with /start")

# ---------- VERIFY CALLBACK ----------
async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id in load_blocked():
        await query.edit_message_text("⛔ You are blocked.")
        return

    if await is_member(user_id, context):
        await query.edit_message_text(
            "✅ Verification successful!\n\n"
            "Now use /start again to access the bot.",
            reply_markup=None
        )
    else:
        await query.edit_message_text(
            "❌ You haven't joined all channels & group yet.\n"
            "Please join and press Verify again.",
            reply_markup=query.message.reply_markup
        )

# ---------- BOT MANAGEMENT CALLBACKS ----------
async def bot_management_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in ADMIN_IDS:
        await query.edit_message_text("⛔ You are not authorized.")
        return

    data = query.data

    if data == "admin_back":
        await query.edit_message_text("🔙 Back to main menu.\nType /start to return.", reply_markup=None)
        return
    elif data == "admin_close":
        await query.edit_message_text("❌ Menu closed. Type /start to reopen.", reply_markup=None)
        return
    elif data == "admin_bot_messenger":
        await query.edit_message_text(
            "🤖 **Bot Messenger**\n\n"
            "Select what you want to send to all users:",
            reply_markup=get_bot_messenger_keyboard()
        )
        return
    elif data == "admin_givecoin":
        context.user_data["admin_action"] = "givecoin"
        await query.edit_message_text(
            "🎁 **Give Coin**\n\nSend the user ID and amount in this format:\n`6496488468 50`\n\nExample: `8670581725 100`",
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "admin_giveallcoins":
        context.user_data["admin_action"] = "giveallcoins"
        await query.edit_message_text(
            "🎁 **Give All Users Coin**\n\nSend the amount to add to every user's balance.\nExample: `10`",
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "admin_query_scope":
        log = load_query_log()
        if not log:
            msg = "📊 No activity logged yet."
        else:
            recent = log[-20:][::-1]
            lines = []
            for entry in recent:
                user = entry.get("name", "Unknown")
                uid = entry.get("user_id", "?")
                qtype = entry.get("type", "").upper()
                qval = entry.get("query", "")
                lines.append(f"👤 {user} (ID: `{uid}`)")
                lines.append(f"🔍 {qtype}: `{qval}`")
                lines.append("")
            msg = "📊 **QueryScope (Recent Activity)**\n\n" + "\n".join(lines)
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_back_keyboard())
        return
    elif data == "admin_stats":
        stats_data = load_data()
        total = len(stats_data)
        total_coins = sum(d.get("coins", 0) for d in stats_data.values())
        blocked = len(load_blocked())
        msg = f"📊 **Bot Statistics**\n👥 Total Users: {total}\n🪙 Total Coins: {total_coins}\n🚫 Blocked: {blocked}"
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_back_keyboard())
        return
    elif data == "admin_block":
        context.user_data["admin_action"] = "block"
        await query.edit_message_text("🚫 **Block User**\n\nSend the user ID you want to block.", reply_markup=get_back_keyboard())
        return
    elif data == "admin_unblock":
        context.user_data["admin_action"] = "unblock"
        await query.edit_message_text("✅ **Unblock User**\n\nSend the user ID you want to unblock.", reply_markup=get_back_keyboard())
        return
    elif data == "admin_blocked_users":
        blocked_set = load_blocked()
        if blocked_set:
            blocked_list = "\n".join(str(uid) for uid in blocked_set)
            msg = f"🚫 **Blocked Users**\n\n{blocked_list}"
        else:
            msg = "✅ No blocked users."
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_back_keyboard())
        return
    elif data == "admin_all_users":
        all_data = load_data()
        if not all_data:
            msg = "No users yet."
        else:
            lines = []
            for uid, info in all_data.items():
                name = info.get("name", "Unknown")
                phone = info.get("phone") or "N/A"
                lines.append(f"`{uid}`")
                lines.append(f"{name}")
                lines.append(f"{phone}")
                lines.append("")
            msg = "👥 **All Users**\n\n" + "\n".join(lines)
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_back_keyboard())
        return

# ---------- BOT MESSENGER CALLBACK HANDLERS ----------
async def messenger_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in ADMIN_IDS:
        await query.edit_message_text("⛔ You are not authorized.")
        return

    data = query.data

    if data == "msg_text":
        context.user_data["admin_action"] = "msg_text"
        await query.edit_message_text(
            "📝 **Send Text Message**\n\n"
            "Type the message you want to broadcast to all users:",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "msg_photo":
        context.user_data["admin_action"] = "msg_photo"
        await query.edit_message_text(
            "🖼️ **Send Photo**\n\n"
            "Send a photo to broadcast to all users.\n"
            "You can add a caption too.",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "msg_video":
        context.user_data["admin_action"] = "msg_video"
        await query.edit_message_text(
            "🎥 **Send Video**\n\n"
            "Send a video (MP4) to broadcast to all users.\n"
            "You can add a caption too.",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "msg_audio":
        context.user_data["admin_action"] = "msg_audio"
        await query.edit_message_text(
            "🎵 **Send Audio/Song**\n\n"
            "Send an audio file (MP3) to broadcast to all users.\n"
            "You can add a caption too.",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "msg_document":
        context.user_data["admin_action"] = "msg_document"
        await query.edit_message_text(
            "📄 **Send Document**\n\n"
            "Send a document (PDF/DOCX) to broadcast to all users.\n"
            "You can add a caption too.",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "msg_gif":
        context.user_data["admin_action"] = "msg_gif"
        await query.edit_message_text(
            "🎞️ **Send GIF**\n\n"
            "Send a GIF to broadcast to all users.\n"
            "You can add a caption too.",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "admin_back":
        await query.edit_message_text("🔙 Back to main menu.\nType /start to return.", reply_markup=None)
        return

# ---------- HANDLE MESSAGES ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""

    # ---- CONTINUOUS VERIFICATION CHECK ----
    if not await is_verified(user_id, context):
        keyboard = []
        keyboard.append([InlineKeyboardButton("📢 𝘫𝘰𝘪𝘯 𝘤𝘩𝘢𝘯𝘯𝘦𝘭 𝟣", url=CHANNELS[0]["link"])])
        keyboard.append([InlineKeyboardButton("📢 𝘫𝘰𝘪𝘯 𝘤𝘩𝘢𝘯𝘯𝘦𝘭 𝟤", url=CHANNELS[1]["link"])])
        keyboard.append([InlineKeyboardButton("📢 𝘫𝘰𝘪𝘯 𝘤𝘩𝘢𝘯𝘯𝘦𝘭 𝟥", url=CHANNELS[2]["link"])])
        keyboard.append([InlineKeyboardButton("👥 𝘫𝘰𝘪𝘯 𝘨𝘳𝘰𝘶𝘱", url=CHANNELS[3]["link"])])
        keyboard.append([InlineKeyboardButton("✅ Verify", callback_data="verify")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ You must be a member of all channels & group to use this bot.\n"
            "Please join and then press Verify.",
            reply_markup=reply_markup
        )
        return

    # ---- ADMIN ACTIONS ----
    if user_id in ADMIN_IDS and context.user_data.get("admin_action"):
        action = context.user_data["admin_action"]

        if action == "msg_text":
            if text and len(text.strip()) > 0:
                data = load_data()
                count = 0
                for uid in data:
                    try:
                        await context.bot.send_message(chat_id=int(uid), text=text)
                        count += 1
                    except:
                        pass
                await update.message.reply_text(f"📝 Text message sent to **{count}** users.")
                context.user_data.pop("admin_action")
                return
            else:
                await update.message.reply_text("❌ Please send a valid text message.")
                return

        elif action == "givecoin":
            parts = text.split()
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                target = int(parts[0])
                amount = int(parts[1])
                data = load_data()
                if str(target) in data:
                    data[str(target)]["coins"] += amount
                    new_total = data[str(target)]["coins"]
                    save_data(data)
                    resp = {
                        "giveaway": False,
                        "added_now": amount,
                        "total_coins": new_total,
                        "status": "active",
                        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙎𝙄𝙉𝙏 𝘾𝙝𝙖𝙣𝙣𝙚𝙡𓆪"
                    }
                    await update.message.reply_text(f"```json\n{json.dumps(resp, indent=2)}\n```", parse_mode="Markdown")
                else:
                    await update.message.reply_text("❌ User not found.")
            else:
                await update.message.reply_text("❌ Invalid format. Use: `USER_ID AMOUNT`", parse_mode="Markdown")
            context.user_data.pop("admin_action")
            return
        elif action == "giveallcoins":
            if text.isdigit():
                amount = int(text)
                data = load_data()
                count = 0
                total_added = 0
                for uid in data:
                    data[uid]["coins"] += amount
                    total_added += amount
                    count += 1
                save_data(data)
                resp = {
                    "giveaway": True,
                    "added_now": amount,
                    "total_coins": total_added,
                    "status": "active",
                    "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙎𝙄𝙉𝙏 𝘾𝙝𝙖𝙣𝙣𝙚𝙡𓆪"
                }
                await update.message.reply_text(f"✅ Added {amount} coins to {count} users.\n```json\n{json.dumps(resp, indent=2)}\n```", parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ Invalid amount. Send a number.")
            context.user_data.pop("admin_action")
            return
        elif action == "block":
            if text.isdigit():
                blocked = load_blocked()
                blocked.add(int(text))
                save_blocked(blocked)
                await update.message.reply_text(f"🚫 User {text} blocked.")
            else:
                await update.message.reply_text("❌ Invalid user ID.")
            context.user_data.pop("admin_action")
            return
        elif action == "unblock":
            if text.isdigit():
                blocked = load_blocked()
                blocked.discard(int(text))
                save_blocked(blocked)
                await update.message.reply_text(f"✅ User {text} unblocked.")
            else:
                await update.message.reply_text("❌ Invalid user ID.")
            context.user_data.pop("admin_action")
            return
        elif action in ["msg_photo", "msg_video", "msg_audio", "msg_document", "msg_gif"]:
            pass

    # ---- LOOKUP COMMANDS ----
    if text == "📱 𝘕𝘶𝘮𝘣𝘦𝘳 𝘓𝘰𝘰𝘬𝘶𝘱":
        await update.message.reply_text("📞 Send a phone number (e.g., 9876543210):")
        context.user_data["lookup_type"] = "number"
    elif text == "🏦 𝘐𝘍𝘚𝘊 𝘓𝘰𝘰𝘬𝘶𝘱":
        await update.message.reply_text("🏦 Send an IFSC code (e.g., SBIN0001234):")
        context.user_data["lookup_type"] = "ifsc"
    elif text == "📍 𝘗𝘪𝘯 𝘊𝘰𝘥𝘦":
        await update.message.reply_text("📮 Send a PIN code (e.g., 110001):")
        context.user_data["lookup_type"] = "pincode"
    elif text == "☁️ 𝘞𝘦𝘢𝘵𝘩𝘦𝘳 𝘓𝘰𝘰𝘬𝘶𝘱":
        await update.message.reply_text("🌤️ Send a city name (e.g., Delhi):")
        context.user_data["lookup_type"] = "weather"
    elif text == "📧 𝘌𝘮𝘢𝘪𝘭 𝘓𝘰𝘰𝘬𝘶𝘱":
        await update.message.reply_text("📧 Send an email address:")
        context.user_data["lookup_type"] = "email"
    elif text == "🪪 𝘈𝘥𝘩𝘢𝘢𝘳 𝘓𝘰𝘰𝘬𝘶𝘱":
        await update.message.reply_text("🆔 Send an Aadhar number (12 digits):")
        context.user_data["lookup_type"] = "aadhar"
    elif text == "🌐 𝘐𝘗 𝘓𝘰𝘰𝘬𝘶𝘱":
        await update.message.reply_text("🌐 Send an IP address (e.g., 8.8.8.8):")
        context.user_data["lookup_type"] = "ip"
    elif text == "💳 𝘗𝘢𝘯 𝘓𝘰𝘰𝘬𝘶𝘱":
        await update.message.reply_text("🆔 Send a PAN number (e.g., ABCDE1234F):")
        context.user_data["lookup_type"] = "pan"
    elif text == "🔢 𝘛𝘎 𝘵𝘰 𝘕𝘶𝘮":
        await update.message.reply_text("🔢 Send a Telegram User ID (e.g., 8497389368):")
        context.user_data["lookup_type"] = "tg_to_num"
    elif text == "👤 𝘔𝘺 𝘈𝘤𝘤𝘰𝘶𝘯𝘵":
        user_data = get_user_data(user_id)
        history = user_data.get("history", [])
        hist_str = "\n".join(history[-5:]) if history else "No history"
        msg = f"👤 **Your Account**\n🪙 Coins: {user_data['coins']}\n👥 Referrals: {user_data['referrals']}\n📜 History:\n{hist_str}"
        await update.message.reply_text(msg, parse_mode="Markdown")
    elif text == "🔗 𝘙𝘦𝘧𝘦𝘳𝘳𝘢𝘭":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        await update.message.reply_text(f"🔗 **Referral Link**\n\nShare this link to earn {REFERRAL_BONUS} coins per referral!\n\n{ref_link}")
    elif text == "🛠️ 𝘉𝘰𝘵 𝘔𝘢𝘯𝘢𝘨𝘦𝘮𝘦𝘯𝘵" and user_id in ADMIN_IDS:
        await update.message.reply_text("🛠️ Bot Management:", reply_markup=get_bot_management_menu())
    else:
        if context.user_data.get("lookup_type"):
            lookup_type = context.user_data.pop("lookup_type")
            await perform_lookup(update, context, lookup_type, text)
        else:
            await update.message.reply_text("🤖 Use the buttons or /start.")

# ---------- MEDIA HANDLERS FOR BOT MESSENGER ----------
async def handle_messenger_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    if context.user_data.get("admin_action") == "msg_photo":
        photo = update.message.photo[-1].file_id
        caption = update.message.caption or ""
        data = load_data()
        count = 0
        for uid in data:
            try:
                await context.bot.send_photo(chat_id=int(uid), photo=photo, caption=caption)
                count += 1
            except:
                pass
        await update.message.reply_text(f"🖼️ Photo sent to {count} users.")
        context.user_data.pop("admin_action")

async def handle_messenger_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    if context.user_data.get("admin_action") == "msg_video":
        video = update.message.video.file_id
        caption = update.message.caption or ""
        data = load_data()
        count = 0
        for uid in data:
            try:
                await context.bot.send_video(chat_id=int(uid), video=video, caption=caption)
                count += 1
            except:
                pass
        await update.message.reply_text(f"🎥 Video sent to {count} users.")
        context.user_data.pop("admin_action")

async def handle_messenger_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    if context.user_data.get("admin_action") == "msg_audio":
        audio = update.message.audio.file_id
        caption = update.message.caption or ""
        data = load_data()
        count = 0
        for uid in data:
            try:
                await context.bot.send_audio(chat_id=int(uid), audio=audio, caption=caption)
                count += 1
            except:
                pass
        await update.message.reply_text(f"🎵 Audio sent to {count} users.")
        context.user_data.pop("admin_action")

async def handle_messenger_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    if context.user_data.get("admin_action") == "msg_document":
        doc = update.message.document.file_id
        caption = update.message.caption or ""
        data = load_data()
        count = 0
        for uid in data:
            try:
                await context.bot.send_document(chat_id=int(uid), document=doc, caption=caption)
                count += 1
            except:
                pass
        await update.message.reply_text(f"📄 Document sent to {count} users.")
        context.user_data.pop("admin_action")

async def handle_messenger_gif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    if context.user_data.get("admin_action") == "msg_gif":
        if update.message.animation:
            gif = update.message.animation.file_id
            caption = update.message.caption or ""
            data = load_data()
            count = 0
            for uid in data:
                try:
                    await context.bot.send_animation(chat_id=int(uid), animation=gif, caption=caption)
                    count += 1
                except:
                    pass
            await update.message.reply_text(f"🎞️ GIF sent to {count} users.")
            context.user_data.pop("admin_action")
            return
        elif update.message.document:
            doc = update.message.document.file_id
            caption = update.message.caption or ""
            data = load_data()
            count = 0
            for uid in data:
                try:
                    await context.bot.send_document(chat_id=int(uid), document=doc, caption=caption)
                    count += 1
                except:
                    pass
            await update.message.reply_text(f"🎞️ GIF (as document) sent to {count} users.")
            context.user_data.pop("admin_action")
            return
        else:
            await update.message.reply_text("❌ Please send a valid GIF file.")
            return

# ---------- FLASK WEB SERVER ----------
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!", 200

@app.route('/ping')
def ping():
    return "Pong!", 200

def run_web():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))

# ---------- MAIN ----------
def main():
    threading.Thread(target=run_web, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()

    # Commands - Only /start and /restart
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("restart", restart))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(verify_callback, pattern="verify"))
    application.add_handler(CallbackQueryHandler(bot_management_callback, pattern="admin_.*"))
    application.add_handler(CallbackQueryHandler(messenger_callback, pattern="msg_.*"))

    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Bot Messenger media handlers - only for admin
    admin_id = ADMIN_IDS[0] if ADMIN_IDS else None
    if admin_id:
        application.add_handler(MessageHandler(filters.PHOTO & filters.User(admin_id), handle_messenger_photo))
        application.add_handler(MessageHandler(filters.VIDEO & filters.User(admin_id), handle_messenger_video))
        application.add_handler(MessageHandler(filters.AUDIO & filters.User(admin_id), handle_messenger_audio))
        application.add_handler(MessageHandler(filters.Document.ALL & filters.User(admin_id), handle_messenger_document))
        application.add_handler(MessageHandler(filters.ANIMATION & filters.User(admin_id), handle_messenger_gif))

    application.run_polling()

if __name__ == "__main__":
    main()
