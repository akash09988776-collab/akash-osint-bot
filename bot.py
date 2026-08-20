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
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "8670581725").split(",")]

# ---------- CHANNELS (4 TOTAL) ----------
CHANNELS = [
    {"name": "Channel 1", "username": "@wftis_ak4sh", "link": "https://t.me/wftis_ak4sh"},
    {"name": "Channel 2", "username": "@Err9r403", "link": "https://t.me/Err9r403"},
    {"name": "Channel 3", "username": "@AkashOSINT", "link": "https://t.me/AkashOSINT"},
    {"name": "Group GC", "username": "+EfWs0w63dYgwNTg1", "link": "https://t.me/+EfWs0w63dYgwNTg1"}
]

# ---------- API URLs ----------
API_NUMBER = "https://travelers-creature-sarah-rogers.trycloudflare.com/search?q={}"
API_IFSC = "https://vercei-kappa.vercel.app/ifsc?code={}"
API_PINCODE = "https://nitin-apis-update-birthday-spacial.vercel.app/api?type=pincode&search={}"
API_WEATHER = "https://nitin-wather-check-api.vercel.app/api?type=weather&search={}"
API_EMAIL = "https://travelers-creature-sarah-rogers.trycloudflare.com/search?q={}"
API_AADHAR = "https://travelers-creature-sarah-rogers.trycloudflare.com/search?q={}"
API_IP = "https://talks-chain-restrictions-statistics.trycloudflare.com/search?query={}"
API_PAN = "https://counted-developing-parade-man.trycloudflare.com/pan-info?pan={}"

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
        ["🅽🆄🅼🅱🅴🆁 🅸🅽🅵🅾", "🆆🅴🅰🆃🅷🅴🆁", "🅿🅸🅽🅲🅾🅳🅴"],
        ["🅸🅵🆂🅲", "🅴🅼🅰🅸🅻 🅸🅽🅵🅾"],
        ["🅰🅰🅳🅷🅰🆁 🅸🅽🅵🅾", "🅸🅿 🅸🅽🅵🅾"],
        ["🅿🅰🅽 🅸🅽🅵🅾"],
        ["🅼🆈 🅰🅲🅲🅾🆄🅽🆃", "🅼🆈 🅲🅾🅸🅽🆂"],
        ["🅼🆈 🅷🅸🆂🆃🅾🆁🆈", "🆁🅴🅵🅴🆁🆁🅰🅻"]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)

def get_admin_keyboard():
    buttons = [
        ["🅽🆄🅼🅱🅴🆁 🅸🅽🅵🅾", "🆆🅴🅰🆃🅷🅴🆁", "🅿🅸🅽🅲🅾🅳🅴"],
        ["🅸🅵🆂🅲", "🅴🅼🅰🅸🅻 🅸🅽🅵🅾"],
        ["🅰🅰🅳🅷🅰🆁 🅸🅽🅵🅾", "🅸🅿 🅸🅽🅵🅾"],
        ["🅿🅰🅽 🅸🅽🅵🅾"],
        ["🅼🆈 🅰🅲🅲🅾🆄🅽🆃", "🅼🆈 🅲🅾🅸🅽🆂"],
        ["🅼🆈 🅷🅸🆂🆃🅾🆁🆈"],
        ["🅾🆆🅽🅴🆁 🅼🅰🅽🅰🅶🅴"]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)

def get_owner_menu():
    keyboard = [
        [InlineKeyboardButton("🎁 𝘎𝘪𝘷𝘦 𝘊𝘰𝘪𝘯", callback_data="admin_givecoin")],
        [InlineKeyboardButton("🎁 𝘎𝘪𝘷𝘦 𝘈𝘭𝘭 𝘜𝘴𝘦𝘳𝘴 𝘊𝘰𝘪𝘯", callback_data="admin_giveallcoins")],
        [InlineKeyboardButton("🤖 𝘉𝘰𝘵 𝘔𝘦𝘴𝘴𝘦𝘯𝘨𝘦𝘳", callback_data="admin_bot_messenger")],
        [InlineKeyboardButton("📊 𝘚𝘵𝘢𝘵𝘴", callback_data="admin_stats")],
        [InlineKeyboardButton("📊 𝘘𝘶𝘦𝘳𝘺𝘚𝘤𝘰𝘱𝘦", callback_data="admin_query_scope")],
        [InlineKeyboardButton("🚫 𝘉𝘭𝘰𝘤𝘬 𝘜𝘴𝘦𝘳", callback_data="admin_block")],
        [InlineKeyboardButton("✅ 𝘜𝘯𝘣𝘭𝘰𝘤𝘬 𝘜𝘴𝘦𝘳", callback_data="admin_unblock")],
        [InlineKeyboardButton("👥 𝘈𝘭𝘭 𝘜𝘴𝘦𝘳𝘴", callback_data="admin_all_users")],
        [InlineKeyboardButton("🚫 𝘉𝘭𝘰𝘤𝘬𝘦𝘥 𝘜𝘴𝘦𝘳𝘴", callback_data="admin_blocked_users")],
        [InlineKeyboardButton("❌ 𝘊𝘭𝘰𝘴𝘦", callback_data="admin_close")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 𝘉𝘢𝘤𝘬", callback_data="admin_back")]]
    return InlineKeyboardMarkup(keyboard)

def get_bot_messenger_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 𝘛𝘦𝘹𝘵 𝘔𝘦𝘴𝘴𝘢𝘨𝘦", callback_data="msg_text")],
        [InlineKeyboardButton("🖼️ 𝘗𝘩𝘰𝘵𝘰", callback_data="msg_photo")],
        [InlineKeyboardButton("🎥 𝘝𝘪𝘥𝘦𝘰", callback_data="msg_video")],
        [InlineKeyboardButton("🎵 𝘈𝘶𝘥𝘪𝘰/𝘚𝘰𝘯𝘨", callback_data="msg_audio")],
        [InlineKeyboardButton("📄 𝘋𝘰𝘤𝘶𝘮𝘦𝘯𝘵", callback_data="msg_document")],
        [InlineKeyboardButton("🎞️ 𝘎𝘐𝘍", callback_data="msg_gif")],
        [InlineKeyboardButton("🔙 𝘉𝘢𝘤𝘬", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_keyboard(user_id=None):
    if user_id and user_id in ADMIN_IDS:
        return get_admin_keyboard()
    return get_user_keyboard()

# ---------- FORMAT FUNCTIONS ----------
def format_number_output(data):
    if not data:
        return "❌ 𝘕𝘰 𝘳𝘦𝘴𝘶𝘭𝘵𝘴 𝘧𝘰𝘶𝘯𝘥."
    results = []
    if isinstance(data, dict):
        if "results" in data:
            results = data["results"]
        elif "data" in data and isinstance(data["data"], dict) and "results" in data["data"]:
            results = data["data"]["results"]
        elif "data" in data and isinstance(data["data"], list):
            results = data["data"]
    if not results:
        out = "**𝙽𝚞𝚖𝚋𝚎𝚛 𝙻𝚘𝚘𝚔𝚞𝚙**\n```json\n"
        out += json.dumps(data, indent=4, ensure_ascii=False)
        out += "\n```"
        return out
    clean_results = []
    for record in results:
        clean_record = {}
        for key, value in record.items():
            if value is not None and value != "":
                clean_record[key] = value
        if clean_record:
            clean_results.append(clean_record)
    clean_data = {
        "total_records": len(clean_results),
        "data": clean_results,
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    out = "**𝙽𝚞𝚖𝚋𝚎𝚛 𝙻𝚘𝚘𝚔𝚞𝚙**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_ifsc_output(data):
    if not data:
        return "❌ 𝘕𝘰 𝘐𝘍𝘚𝘊 𝘥𝘦𝘵𝘢𝘪𝘭𝘴 𝘧𝘰𝘶𝘯𝘥."
    if "success" in data and data["success"] == False:
        return "❌ 𝘕𝘰 𝘐𝘍𝘚𝘊 𝘥𝘦𝘵𝘢𝘪𝘭𝘴 𝘧𝘰𝘶𝘯𝘥."
    ifsc_data = data
    if "data" in data and isinstance(data["data"], dict):
        ifsc_data = data["data"]
    clean_data = {}
    for key, value in ifsc_data.items():
        if value is not None and value != "":
            clean_data[key] = value
    if not clean_data:
        return "❌ 𝘕𝘰 𝘐𝘍𝘚𝘊 𝘥𝘦𝘵𝘢𝘪𝘭𝘴 𝘧𝘰𝘶𝘯𝘥."
    clean_data["developer"] = "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    out = "**𝙸𝙵𝚂𝙲 𝙻𝚘𝚘𝚔𝚞𝚙**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_pincode_output(data):
    if not data or data.get("status") != "success":
        return "❌ 𝘕𝘰 𝘗𝘐𝘕 𝘤𝘰𝘥𝘦 𝘥𝘦𝘵𝘢𝘪𝘭𝘴 𝘧𝘰𝘶𝘯𝘥."
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
    out = "**𝙿𝙸𝙽 𝙲𝚘𝚍𝚎 𝚂𝚎𝚊𝚛𝚌𝚑**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_weather_output(data):
    if not data or not data.get("success") or not data.get("data"):
        return "❌ 𝘕𝘰 𝘸𝘦𝘢𝘵𝘩𝘦𝘳 𝘥𝘢𝘵𝘢 𝘧𝘰𝘶𝘯𝘥."
    w = data["data"]
    city = w.get("city", {})
    current = w.get("current", {})
    forecast = w.get("forecast", {}).get("daily_7day", [])
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
    out = "**𝚆𝚎𝚊𝚝𝚑𝚎𝚛 𝙲𝚑𝚎𝚌𝚔**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_email_output(data):
    if not data:
        return "❌ 𝘕𝘰 𝘦𝘮𝘢𝘪𝘭 𝘥𝘦𝘵𝘢𝘪𝘭𝘴 𝘧𝘰𝘶𝘯𝘥."
    results = []
    query = None
    success = True
    if isinstance(data, dict):
        success = data.get("success", True)
        query = data.get("query") or data.get("q")
        if "results" in data:
            results = data["results"]
        elif "data" in data and isinstance(data["data"], dict) and "results" in data["data"]:
            results = data["data"]["results"]
        elif "data" in data and isinstance(data["data"], list):
            results = data["data"]
    if not results:
        out = "**𝙴𝚖𝚊𝚒𝚕 𝙸𝚗𝚏𝚘**\n```json\n"
        out += json.dumps(data, indent=4, ensure_ascii=False)
        out += "\n```"
        return out
    clean_data = {
        "success": success,
        "query": query or "N/A",
        "total_found": len(results),
        "results": results,
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    out = "**𝙴𝚖𝚊𝚒𝚕 𝙸𝚗𝚏𝚘**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_aadhar_output(data):
    if not data:
        return "❌ 𝘕𝘰 𝘈𝘢𝘥𝘩𝘢𝘳 𝘥𝘦𝘵𝘢𝘪𝘭𝘴 𝘧𝘰𝘶𝘯𝘥."
    results = []
    query = None
    success = True
    if isinstance(data, dict):
        success = data.get("success", True)
        query = data.get("query") or data.get("q")
        if "results" in data:
            results = data["results"]
        elif "data" in data and isinstance(data["data"], dict) and "results" in data["data"]:
            results = data["data"]["results"]
        elif "data" in data and isinstance(data["data"], list):
            results = data["data"]
    if not results:
        out = "**𝙰𝚊𝚍𝚑𝚊𝚛 𝙸𝚗𝚏𝚘**\n```json\n"
        out += json.dumps(data, indent=4, ensure_ascii=False)
        out += "\n```"
        return out
    clean_data = {
        "success": success,
        "query": query or "N/A",
        "total_found": len(results),
        "results": results,
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    out = "**𝙰𝚊𝚍𝚑𝚊𝚛 𝙸𝚗𝚏𝚘**\n```json\n"
    out += json.dumps(clean_data, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_ip_output(data):
    if not data:
        return "❌ 𝘕𝘰 𝘐𝘗 𝘥𝘦𝘵𝘢𝘪𝘭𝘴 𝘧𝘰𝘶𝘯𝘥."
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
        out = "**𝙸𝙿 𝙸𝚗𝚏𝚘**\n```json\n"
        out += json.dumps(data, indent=4, ensure_ascii=False)
        out += "\n```"
        return out
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
    result = {
        "total_records": len(cleaned_records),
        "data": cleaned_records,
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    out = "**𝙸𝙿 𝙸𝚗𝚏𝚘**\n```json\n"
    out += json.dumps(result, indent=4, ensure_ascii=False)
    out += "\n```"
    return out

def format_pan_output(data):
    if not data:
        return "❌ 𝘕𝘰 𝘗𝘈𝘕 𝘥𝘦𝘵𝘢𝘪𝘭𝘴 𝘧𝘰𝘶𝘯𝘥."
    results = []
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            results = data["data"]
        elif "data" in data and isinstance(data["data"], dict):
            results = [data["data"]]
        elif "results" in data:
            results = data["results"]
    if not results:
        if isinstance(data, dict) and "pan" in data:
            results = [data]
        else:
            out = "**𝙿𝙰𝙽 𝙸𝚗𝚏𝚘**\n```json\n"
            out += json.dumps(data, indent=4, ensure_ascii=False)
            out += "\n```"
            return out
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
    result = {
        "total_records": len(clean_results),
        "data": clean_results,
        "developer": "𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤"
    }
    out = "**𝙿𝙰𝙽 𝙸𝚗𝚏𝚘**\n```json\n"
    out += json.dumps(result, indent=4, ensure_ascii=False)
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
            await update.message.reply_text("❌ 𝘕𝘰𝘵 𝘦𝘯𝘰𝘶𝘨𝘩 𝘤𝘰𝘪𝘯𝘴. 𝘌𝘢𝘳𝘯 𝘷𝘪𝘢 𝘳𝘦𝘧𝘦𝘳𝘳𝘢𝘭𝘴!")
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
    else:
        await update.message.reply_text("❌ 𝘜𝘯𝘬𝘯𝘰𝘸𝘯 𝘭𝘰𝘰𝘬𝘶𝘱.")
        return

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"_raw": response.text}
    except Exception:
        await update.message.reply_text("❌ 𝘕𝘰 𝘳𝘦𝘴𝘶𝘭𝘵𝘴 𝘧𝘰𝘶𝘯𝘥 𝘰𝘳 𝘴𝘦𝘳𝘷𝘪𝘤𝘦 𝘶𝘯𝘢𝘷𝘢𝘪𝘭𝘢𝘣𝘭𝘦. 𝘗𝘭𝘦𝘢𝘴𝘦 𝘵𝘳𝘺 𝘢𝘨𝘢𝘪𝘯 𝘭𝘢𝘵𝘦𝘳.")
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
        await update.message.reply_text("⛔ 𝘠𝘰𝘶 𝘢𝘳𝘦 𝘣𝘭𝘰𝘤𝘬𝘦𝘥 𝘧𝘳𝘰𝘮 𝘶𝘴𝘪𝘯𝘨 𝘵𝘩𝘪𝘴 𝘣𝘰𝘵.")
        return

    if await is_verified(user_id, context):
        welcome = (
            f"𝑯𝒆𝒚 👋 {first_name}\n\n"
            f"𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𐙚 𓆩𝘼𝙠𝙖𝙨𝙝 𝙊𝙨𝙞𝙣𝙩𓆪𓂃🧑‍💻🎀⃤𝑩𝒐𝒕 /~❤️\n"
            f"𝑼𝒔𝒆𝒓 𝑰𝑫 ➜ {user_id} ❤️\n\n"
            f"𝘠𝘰𝘶 𝘢𝘳𝘦 𝘷𝘦𝘳𝘪𝘧𝘪𝘦𝘥!\n𝘜𝘴𝘦 𝘵𝘩𝘦 𝘣𝘶𝘵𝘵𝘰𝘯𝘴 𝘣𝘦𝘭𝘰𝘸."
        )
        await update.message.reply_text(welcome, reply_markup=get_keyboard(user_id))
        return

    # ---- 4 ALIGNED BUTTONS WITH CUSTOM FONT ----
    keyboard = [
        [InlineKeyboardButton("📢 𝘫𝘰𝘪𝘯 𝘤𝘩𝘢𝘯𝘯𝘦𝘭 𝟣", url=CHANNELS[0]["link"])],
        [InlineKeyboardButton("📢 𝘫𝘰𝘪𝘯 𝘤𝘩𝘢𝘯𝘯𝘦𝘭 𝟤", url=CHANNELS[1]["link"])],
        [InlineKeyboardButton("📢 𝘫𝘰𝘪𝘯 𝘤𝘩𝘢𝘯𝘯𝘦𝘭 𝟥", url=CHANNELS[2]["link"])],
        [InlineKeyboardButton("👥 𝘫𝘰𝘪𝘯 𝘨𝘳𝘰𝘶𝘱", url=CHANNELS[3]["link"])],
        [InlineKeyboardButton("✅ 𝘷𝘦𝘳𝘪𝘧𝘺", callback_data="verify")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "𝑷𝒍𝒆𝒂𝒔𝒆 𝒋𝒐𝒊𝒏 𝒂𝒍𝒍 𝟰 𝒄𝒉𝒂𝒏𝒏𝒆𝒍𝒔 𝒕𝒐 𝒖𝒔𝒆 𝒕𝒉𝒊𝒔 𝒃𝒐𝒕:\n\n"
        "𝘈𝘧𝘵𝘦𝘳 𝘫𝘰𝘪𝘯𝘪𝘯𝘨, 𝘱𝘳𝘦𝘴𝘴 𝘵𝘩𝘦 𝘝𝘦𝘳𝘪𝘧𝘺 𝘣𝘶𝘵𝘵𝘰𝘯.",
        reply_markup=reply_markup
    )

# ---------- RESTART COMMAND ----------
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        await update.message.reply_text("🔄 𝘉𝘰𝘵 𝘪𝘴 𝘳𝘦𝘴𝘵𝘢𝘳𝘵𝘪𝘯𝘨...")
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        await update.message.reply_text("❌ 𝘠𝘰𝘶 𝘢𝘳𝘦 𝘯𝘰𝘵 𝘢𝘶𝘵𝘩𝘰𝘳𝘪𝘻𝘦𝘥 𝘵𝘰 𝘳𝘦𝘴𝘵𝘢𝘳𝘵 𝘵𝘩𝘦 𝘣𝘰𝘵.")

# ---------- SET PHONE COMMAND ----------
async def setphone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘴𝘦𝘯𝘥 𝘺𝘰𝘶𝘳 𝘱𝘩𝘰𝘯𝘦 𝘯𝘶𝘮𝘣𝘦𝘳 𝘭𝘪𝘬𝘦:\n`/setphone +917250385668`", parse_mode="Markdown")
        return
    phone = " ".join(context.args).strip()
    if len(re.sub(r'\D', '', phone)) < 10:
        await update.message.reply_text("❌ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘱𝘩𝘰𝘯𝘦 𝘯𝘶𝘮𝘣𝘦𝘳. 𝘗𝘭𝘦𝘢𝘴𝘦 𝘪𝘯𝘤𝘭𝘶𝘥𝘦 𝘤𝘰𝘶𝘯𝘵𝘳𝘺 𝘤𝘰𝘥𝘦 (𝘦.𝘨., +91...)")
        return
    data = load_data()
    uid = str(user_id)
    if uid in data:
        data[uid]["phone"] = phone
        save_data(data)
        await update.message.reply_text(f"✅ 𝘠𝘰𝘶𝘳 𝘱𝘩𝘰𝘯𝘦 𝘯𝘶𝘮𝘣𝘦𝘳 𝘩𝘢𝘴 𝘣𝘦𝘦𝘯 𝘴𝘦𝘵 𝘵𝘰: `{phone}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ 𝘠𝘰𝘶 𝘯𝘦𝘦𝘥 𝘵𝘰 𝘴𝘵𝘢𝘳𝘵 𝘵𝘩𝘦 𝘣𝘰𝘵 𝘧𝘪𝘳𝘴𝘵 𝘸𝘪𝘵𝘩 /start")

# ---------- VERIFY CALLBACK ----------
async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id in load_blocked():
        await query.edit_message_text("⛔ 𝘠𝘰𝘶 𝘢𝘳𝘦 𝘣𝘭𝘰𝘤𝘬𝘦𝘥.")
        return

    if await is_member(user_id, context):
        await query.edit_message_text(
            " 𝘝𝘦𝘳𝘪𝘧𝘪𝘤𝘢𝘵𝘪𝘰𝘯 𝘴𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭!\n\n"
            "𝘕𝘰𝘸 𝘶𝘴𝘦 /start 𝘢𝘨𝘢𝘪𝘯 𝘵𝘰 𝘢𝘤𝘤𝘦𝘴𝘴 𝘵𝘩𝘦 𝘣𝘰𝘵.",
            reply_markup=None
        )
    else:
        await query.edit_message_text(
            "❌ 𝘠𝘰𝘶 𝘩𝘢𝘷𝘦𝘯'𝘵 𝘫𝘰𝘪𝘯𝘦𝘥 𝘢𝘭𝘭 4 𝘤𝘩𝘢𝘯𝘯𝘦𝘭𝘴 𝘺𝘦𝘵.\n"
            "𝘗𝘭𝘦𝘢𝘴𝘦 𝘫𝘰𝘪𝘯 𝘢𝘯𝘥 𝘱𝘳𝘦𝘴𝘴 𝘝𝘦𝘳𝘪𝘧𝘺 𝘢𝘨𝘢𝘪𝘯.",
            reply_markup=query.message.reply_markup
        )

# ---------- OWNER MENU CALLBACKS ----------
async def owner_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in ADMIN_IDS:
        await query.edit_message_text("⛔ 𝘠𝘰𝘶 𝘢𝘳𝘦 𝘯𝘰𝘵 𝘢𝘶𝘵𝘩𝘰𝘳𝘪𝘻𝘦𝘥.")
        return

    data = query.data

    if data == "admin_back":
        await query.edit_message_text("🔙 𝘉𝘢𝘤𝘬 𝘵𝘰 𝘮𝘢𝘪𝘯 𝘮𝘦𝘯𝘶.\n𝘛𝘺𝘱𝘦 /start 𝘵𝘰 𝘳𝘦𝘵𝘶𝘳𝘯.", reply_markup=None)
        return
    elif data == "admin_close":
        await query.edit_message_text("❌ 𝘔𝘦𝘯𝘶 𝘤𝘭𝘰𝘴𝘦𝘥. 𝘛𝘺𝘱𝘦 /start 𝘵𝘰 𝘳𝘦𝘰𝘱𝘦𝘯.", reply_markup=None)
        return
    elif data == "admin_bot_messenger":
        await query.edit_message_text(
            "🤖 **𝘉𝘰𝘵 𝘔𝘦𝘴𝘴𝘦𝘯𝘨𝘦𝘳**\n\n"
            "𝘚𝘦𝘭𝘦𝘤𝘵 𝘸𝘩𝘢𝘵 𝘺𝘰𝘶 𝘸𝘢𝘯𝘵 𝘵𝘰 𝘴𝘦𝘯𝘥 𝘵𝘰 𝘢𝘭𝘭 𝘶𝘴𝘦𝘳𝘴:",
            reply_markup=get_bot_messenger_keyboard()
        )
        return
    elif data == "admin_givecoin":
        context.user_data["admin_action"] = "givecoin"
        await query.edit_message_text(
            "🎁 **𝘎𝘪𝘷𝘦 𝘊𝘰𝘪𝘯**\n\n𝘚𝘦𝘯𝘥 𝘵𝘩𝘦 𝘶𝘴𝘦𝘳 𝘐𝘋 𝘢𝘯𝘥 𝘢𝘮𝘰𝘶𝘯𝘵 𝘪𝘯 𝘵𝘩𝘪𝘴 𝘧𝘰𝘳𝘮𝘢𝘵:\n`6496488468 50`\n\n𝘌𝘹𝘢𝘮𝘱𝘭𝘦: `8670581725 100`",
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "admin_giveallcoins":
        context.user_data["admin_action"] = "giveallcoins"
        await query.edit_message_text(
            "🎁 **𝘎𝘪𝘷𝘦 𝘈𝘭𝘭 𝘜𝘴𝘦𝘳𝘴 𝘊𝘰𝘪𝘯**\n\n𝘚𝘦𝘯𝘥 𝘵𝘩𝘦 𝘢𝘮𝘰𝘶𝘯𝘵 𝘵𝘰 𝘢𝘥𝘥 𝘵𝘰 𝘦𝘷𝘦𝘳𝘺 𝘶𝘴𝘦𝘳'𝘴 𝘣𝘢𝘭𝘢𝘯𝘤𝘦.\n𝘌𝘹𝘢𝘮𝘱𝘭𝘦: `10`",
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "admin_query_scope":
        log = load_query_log()
        if not log:
            msg = "📊 𝘕𝘰 𝘢𝘤𝘵𝘪𝘷𝘪𝘵𝘺 𝘭𝘰𝘨𝘨𝘦𝘥 𝘺𝘦𝘵."
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
            msg = "📊 **𝘘𝘶𝘦𝘳𝘺𝘚𝘤𝘰𝘱𝘦 (𝘙𝘦𝘤𝘦𝘯𝘵 𝘈𝘤𝘵𝘪𝘷𝘪𝘵𝘺)**\n\n" + "\n".join(lines)
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_back_keyboard())
        return
    elif data == "admin_stats":
        stats_data = load_data()
        total = len(stats_data)
        total_coins = sum(d.get("coins", 0) for d in stats_data.values())
        blocked = len(load_blocked())
        msg = f"📊 **𝘉𝘰𝘵 𝘚𝘵𝘢𝘵𝘪𝘴𝘵𝘪𝘤𝘴**\n👥 𝘛𝘰𝘵𝘢𝘭 𝘜𝘴𝘦𝘳𝘴: {total}\n🪙 𝘛𝘰𝘵𝘢𝘭 𝘊𝘰𝘪𝘯𝘴: {total_coins}\n🚫 𝘉𝘭𝘰𝘤𝘬𝘦𝘥: {blocked}"
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_back_keyboard())
        return
    elif data == "admin_block":
        context.user_data["admin_action"] = "block"
        await query.edit_message_text("🚫 **𝘉𝘭𝘰𝘤𝘬 𝘜𝘴𝘦𝘳**\n\n𝘚𝘦𝘯𝘥 𝘵𝘩𝘦 𝘶𝘴𝘦𝘳 𝘐𝘋 𝘺𝘰𝘶 𝘸𝘢𝘯𝘵 𝘵𝘰 𝘣𝘭𝘰𝘤𝘬.", reply_markup=get_back_keyboard())
        return
    elif data == "admin_unblock":
        context.user_data["admin_action"] = "unblock"
        await query.edit_message_text("✅ **𝘜𝘯𝘣𝘭𝘰𝘤𝘬 𝘜𝘴𝘦𝘳**\n\n𝘚𝘦𝘯𝘥 𝘵𝘩𝘦 𝘶𝘴𝘦𝘳 𝘐𝘋 𝘺𝘰𝘶 𝘸𝘢𝘯𝘵 𝘵𝘰 𝘶𝘯𝘣𝘭𝘰𝘤𝘬.", reply_markup=get_back_keyboard())
        return
    elif data == "admin_blocked_users":
        blocked_set = load_blocked()
        if blocked_set:
            blocked_list = "\n".join(str(uid) for uid in blocked_set)
            msg = f"🚫 **𝘉𝘭𝘰𝘤𝘬𝘦𝘥 𝘜𝘴𝘦𝘳𝘴**\n\n{blocked_list}"
        else:
            msg = "✅ 𝘕𝘰 𝘣𝘭𝘰𝘤𝘬𝘦𝘥 𝘶𝘴𝘦𝘳𝘴."
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_back_keyboard())
        return
    elif data == "admin_all_users":
        all_data = load_data()
        if not all_data:
            msg = "👥 𝘕𝘰 𝘶𝘴𝘦𝘳𝘴 𝘺𝘦𝘵."
        else:
            lines = []
            for uid, info in all_data.items():
                name = info.get("name", "Unknown")
                phone = info.get("phone") or "N/A"
                lines.append(f"`{uid}`")
                lines.append(f"{name}")
                lines.append(f"{phone}")
                lines.append("")
            msg = "👥 **𝘈𝘭𝘭 𝘜𝘴𝘦𝘳𝘴**\n\n" + "\n".join(lines)
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_back_keyboard())
        return

# ---------- BOT MESSENGER CALLBACK HANDLERS ----------
async def messenger_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in ADMIN_IDS:
        await query.edit_message_text("⛔ 𝘠𝘰𝘶 𝘢𝘳𝘦 𝘯𝘰𝘵 𝘢𝘶𝘵𝘩𝘰𝘳𝘪𝘻𝘦𝘥.")
        return

    data = query.data

    if data == "msg_text":
        context.user_data["admin_action"] = "msg_text"
        await query.edit_message_text(
            "📝 **𝘚𝘦𝘯𝘥 𝘛𝘦𝘹𝘵 𝘔𝘦𝘴𝘴𝘢𝘨𝘦**\n\n"
            "𝘛𝘺𝘱𝘦 𝘵𝘩𝘦 𝘮𝘦𝘴𝘴𝘢𝘨𝘦 𝘺𝘰𝘶 𝘸𝘢𝘯𝘵 𝘵𝘰 𝘣𝘳𝘰𝘢𝘥𝘤𝘢𝘴𝘵 𝘵𝘰 𝘢𝘭𝘭 𝘶𝘴𝘦𝘳𝘴:",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "msg_photo":
        context.user_data["admin_action"] = "msg_photo"
        await query.edit_message_text(
            "🖼️ **𝘚𝘦𝘯𝘥 𝘗𝘩𝘰𝘵𝘰**\n\n"
            "𝘚𝘦𝘯𝘥 𝘢 𝘱𝘩𝘰𝘵𝘰 𝘵𝘰 𝘣𝘳𝘰𝘢𝘥𝘤𝘢𝘴𝘵 𝘵𝘰 𝘢𝘭𝘭 𝘶𝘴𝘦𝘳𝘴.\n"
            "𝘠𝘰𝘶 𝘤𝘢𝘯 𝘢𝘥𝘥 𝘢 𝘤𝘢𝘱𝘵𝘪𝘰𝘯 𝘵𝘰𝘰.",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "msg_video":
        context.user_data["admin_action"] = "msg_video"
        await query.edit_message_text(
            "🎥 **𝘚𝘦𝘯𝘥 𝘝𝘪𝘥𝘦𝘰**\n\n"
            "𝘚𝘦𝘯𝘥 𝘢 𝘷𝘪𝘥𝘦𝘰 (𝘔𝘗4) 𝘵𝘰 𝘣𝘳𝘰𝘢𝘥𝘤𝘢𝘴𝘵 𝘵𝘰 𝘢𝘭𝘭 𝘶𝘴𝘦𝘳𝘴.\n"
            "𝘠𝘰𝘶 𝘤𝘢𝘯 𝘢𝘥𝘥 𝘢 𝘤𝘢𝘱𝘵𝘪𝘰𝘯 𝘵𝘰𝘰.",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "msg_audio":
        context.user_data["admin_action"] = "msg_audio"
        await query.edit_message_text(
            "🎵 **𝘚𝘦𝘯𝘥 𝘈𝘶𝘥𝘪𝘰/𝘚𝘰𝘯𝘨**\n\n"
            "𝘚𝘦𝘯𝘥 𝘢𝘯 𝘢𝘶𝘥𝘪𝘰 𝘧𝘪𝘭𝘦 (𝘔𝘗3) 𝘵𝘰 𝘣𝘳𝘰𝘢𝘥𝘤𝘢𝘴𝘵 𝘵𝘰 𝘢𝘭𝘭 𝘶𝘴𝘦𝘳𝘴.\n"
            "𝘠𝘰𝘶 𝘤𝘢𝘯 𝘢𝘥𝘥 𝘢 𝘤𝘢𝘱𝘵𝘪𝘰𝘯 𝘵𝘰𝘰.",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "msg_document":
        context.user_data["admin_action"] = "msg_document"
        await query.edit_message_text(
            "📄 **𝘚𝘦𝘯𝘥 𝘋𝘰𝘤𝘶𝘮𝘦𝘯𝘵**\n\n"
            "𝘚𝘦𝘯𝘥 𝘢 𝘥𝘰𝘤𝘶𝘮𝘦𝘯𝘵 (𝘗𝘋𝘍/𝘋𝘖𝘊𝘟) 𝘵𝘰 𝘣𝘳𝘰𝘢𝘥𝘤𝘢𝘴𝘵 𝘵𝘰 𝘢𝘭𝘭 𝘶𝘴𝘦𝘳𝘴.\n"
            "𝘠𝘰𝘶 𝘤𝘢𝘯 𝘢𝘥𝘥 𝘢 𝘤𝘢𝘱𝘵𝘪𝘰𝘯 𝘵𝘰𝘰.",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "msg_gif":
        context.user_data["admin_action"] = "msg_gif"
        await query.edit_message_text(
            "🎞️ **𝘚𝘦𝘯𝘥 𝘎𝘐𝘍**\n\n"
            "𝘚𝘦𝘯𝘥 𝘢 𝘎𝘐𝘍 𝘵𝘰 𝘣𝘳𝘰𝘢𝘥𝘤𝘢𝘴𝘵 𝘵𝘰 𝘢𝘭𝘭 𝘶𝘴𝘦𝘳𝘴.\n"
            "𝘠𝘰𝘶 𝘤𝘢𝘯 𝘢𝘥𝘥 𝘢 𝘤𝘢𝘱𝘵𝘪𝘰𝘯 𝘵𝘰𝘰.",
            reply_markup=get_back_keyboard()
        )
        return
    elif data == "admin_back":
        await query.edit_message_text("🔙 𝘉𝘢𝘤𝘬 𝘵𝘰 𝘮𝘢𝘪𝘯 𝘮𝘦𝘯𝘶.\n𝘛𝘺𝘱𝘦 /start 𝘵𝘰 𝘳𝘦𝘵𝘶𝘳𝘯.", reply_markup=None)
        return

# ---------- HANDLE MESSAGES ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""

    # ---- CONTINUOUS VERIFICATION CHECK ----
    if not await is_verified(user_id, context):
        keyboard = []
        for ch in CHANNELS:
            keyboard.append([InlineKeyboardButton(f"📢 𝘫𝘰𝘪𝘯 {ch['name']}", url=ch["link"])])
        keyboard.append([InlineKeyboardButton("✅ 𝘷𝘦𝘳𝘪𝘧𝘺", callback_data="verify")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ 𝘠𝘰𝘶 𝘮𝘶𝘴𝘵 𝘣𝘦 𝘢 𝘮𝘦𝘮𝘣𝘦𝘳 𝘰𝘧 𝘢𝘭𝘭 4 𝘤𝘩𝘢𝘯𝘯𝘦𝘭𝘴 𝘵𝘰 𝘶𝘴𝘦 𝘵𝘩𝘪𝘴 𝘣𝘰𝘵.\n"
            "𝘗𝘭𝘦𝘢𝘴𝘦 𝘫𝘰𝘪𝘯 𝘢𝘯𝘥 𝘵𝘩𝘦𝘯 𝘱𝘳𝘦𝘴𝘴 𝘝𝘦𝘳𝘪𝘧𝘺.",
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
                await update.message.reply_text(f"📝 𝘛𝘦𝘹𝘵 𝘮𝘦𝘴𝘴𝘢𝘨𝘦 𝘴𝘦𝘯𝘵 𝘵𝘰 **{count}** 𝘶𝘴𝘦𝘳𝘴.")
                context.user_data.pop("admin_action")
                return
            else:
                await update.message.reply_text("❌ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘴𝘦𝘯𝘥 𝘢 𝘷𝘢𝘭𝘪𝘥 𝘵𝘦𝘹𝘵 𝘮𝘦𝘴𝘴𝘢𝘨𝘦.")
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
                    await update.message.reply_text("❌ 𝘜𝘴𝘦𝘳 𝘯𝘰𝘵 𝘧𝘰𝘶𝘯𝘥.")
            else:
                await update.message.reply_text("❌ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘧𝘰𝘳𝘮𝘢𝘵. 𝘜𝘴𝘦: `USER_ID AMOUNT`", parse_mode="Markdown")
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
                await update.message.reply_text(f"✅ 𝘈𝘥𝘥𝘦𝘥 {amount} 𝘤𝘰𝘪𝘯𝘴 𝘵𝘰 {count} 𝘶𝘴𝘦𝘳𝘴.\n```json\n{json.dumps(resp, indent=2)}\n```", parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘢𝘮𝘰𝘶𝘯𝘵. 𝘚𝘦𝘯𝘥 𝘢 𝘯𝘶𝘮𝘣𝘦𝘳.")
            context.user_data.pop("admin_action")
            return
        elif action == "block":
            if text.isdigit():
                blocked = load_blocked()
                blocked.add(int(text))
                save_blocked(blocked)
                await update.message.reply_text(f"🚫 𝘜𝘴𝘦𝘳 {text} 𝘣𝘭𝘰𝘤𝘬𝘦𝘥.")
            else:
                await update.message.reply_text("❌ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘶𝘴𝘦𝘳 𝘐𝘋.")
            context.user_data.pop("admin_action")
            return
        elif action == "unblock":
            if text.isdigit():
                blocked = load_blocked()
                blocked.discard(int(text))
                save_blocked(blocked)
                await update.message.reply_text(f"✅ 𝘜𝘴𝘦𝘳 {text} 𝘶𝘯𝘣𝘭𝘰𝘤𝘬𝘦𝘥.")
            else:
                await update.message.reply_text("❌ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘶𝘴𝘦𝘳 𝘐𝘋.")
            context.user_data.pop("admin_action")
            return
        elif action in ["msg_photo", "msg_video", "msg_audio", "msg_document", "msg_gif"]:
            pass

    # ---- REGULAR COMMANDS (with custom font) ----
    if text.lower() in ["number info", "number", "phone"]:
        await update.message.reply_text("📞 𝘚𝘦𝘯𝘥 𝘢 𝘱𝘩𝘰𝘯𝘦 𝘯𝘶𝘮𝘣𝘦𝘳 (𝘦.𝘨., 9876543210):")
        context.user_data["lookup_type"] = "number"
    elif text.lower() in ["ifsc"]:
        await update.message.reply_text("🏦 𝘚𝘦𝘯𝘥 𝘢𝘯 𝘐𝘍𝘚𝘊 𝘤𝘰𝘥𝘦 (𝘦.𝘨., 𝘚𝘉𝘐𝘕0001234):")
        context.user_data["lookup_type"] = "ifsc"
    elif text.lower() in ["pincode"]:
        await update.message.reply_text("📮 𝘚𝘦𝘯𝘥 𝘢 𝘗𝘐𝘕 𝘤𝘰𝘥𝘦 (𝘦.𝘨., 110001):")
        context.user_data["lookup_type"] = "pincode"
    elif text.lower() in ["wether", "weather"]:
        await update.message.reply_text("🌤️ 𝘚𝘦𝘯𝘥 𝘢 𝘤𝘪𝘵𝘺 𝘯𝘢𝘮𝘦 (𝘦.𝘨., 𝘋𝘦𝘭𝘩𝘪):")
        context.user_data["lookup_type"] = "weather"
    elif text.lower() in ["email info", "email"]:
        await update.message.reply_text("📧 𝘚𝘦𝘯𝘥 𝘢𝘯 𝘦𝘮𝘢𝘪𝘭 𝘢𝘥𝘥𝘳𝘦𝘴𝘴:")
        context.user_data["lookup_type"] = "email"
    elif text.lower() in ["aadhar info", "aadhar"]:
        await update.message.reply_text("🆔 𝘚𝘦𝘯𝘥 𝘢𝘯 𝘈𝘢𝘥𝘩𝘢𝘳 𝘯𝘶𝘮𝘣𝘦𝘳 (12 𝘥𝘪𝘨𝘪𝘵𝘴):")
        context.user_data["lookup_type"] = "aadhar"
    elif text.lower() in ["ip info", "ip"]:
        await update.message.reply_text("🌐 𝘚𝘦𝘯𝘥 𝘢𝘯 𝘐𝘗 𝘢𝘥𝘥𝘳𝘦𝘴𝘴 (𝘦.𝘨., 8.8.8.8):")
        context.user_data["lookup_type"] = "ip"
    elif text.lower() in ["pan info", "pan"]:
        await update.message.reply_text("🆔 𝘚𝘦𝘯𝘥 𝘢 𝘗𝘈𝘕 𝘯𝘶𝘮𝘣𝘦𝘳 (𝘦.𝘨., 𝘈𝘉𝘊𝘋𝘌1234𝘍):")
        context.user_data["lookup_type"] = "pan"
    elif text.lower() in ["my account"]:
        user_data = get_user_data(user_id)
        msg = f"👤 **𝘠𝘰𝘶𝘳 𝘈𝘤𝘤𝘰𝘶𝘯𝘵**\n🪙 𝘊𝘰𝘪𝘯𝘴: {user_data['coins']}\n👥 𝘙𝘦𝘧𝘦𝘳𝘳𝘢𝘭𝘴: {user_data['referrals']}"
        await update.message.reply_text(msg, parse_mode="Markdown")
    elif text.lower() in ["my history"]:
        user_data = get_user_data(user_id)
        history = user_data.get("history", [])
        if history:
            lines = "\n".join(history[-10:])
            msg = f"📜 **𝘠𝘰𝘶𝘳 𝘏𝘪𝘴𝘵𝘰𝘳𝘺**\n{lines}"
        else:
            msg = "📜 𝘕𝘰 𝘩𝘪𝘴𝘵𝘰𝘳𝘺 𝘺𝘦𝘵."
        await update.message.reply_text(msg, parse_mode="Markdown")
    elif text.lower() in ["my coins"]:
        user_data = get_user_data(user_id)
        await update.message.reply_text(f"🪙 𝘠𝘰𝘶 𝘩𝘢𝘷𝘦 {user_data['coins']} 𝘤𝘰𝘪𝘯𝘴.")
    elif text.lower() in ["referral"]:
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        await update.message.reply_text(f"🔗 **𝘙𝘦𝘧𝘦𝘳𝘳𝘢𝘭 𝘓𝘪𝘯𝘬**\n\n𝘚𝘩𝘢𝘳𝘦 𝘵𝘩𝘪𝘴 𝘭𝘪𝘯𝘬 𝘵𝘰 𝘦𝘢𝘳𝘯 {REFERRAL_BONUS} 𝘤𝘰𝘪𝘯𝘴 𝘱𝘦𝘳 𝘳𝘦𝘧𝘦𝘳𝘳𝘢𝘭!\n\n{ref_link}")
    elif text.lower() in ["owner manage"] and user_id in ADMIN_IDS:
        await update.message.reply_text("👑 𝘖𝘸𝘯𝘦𝘳 𝘔𝘦𝘯𝘶:", reply_markup=get_owner_menu())
    else:
        if context.user_data.get("lookup_type"):
            lookup_type = context.user_data.pop("lookup_type")
            await perform_lookup(update, context, lookup_type, text)
        else:
            await update.message.reply_text("🤖 𝘜𝘴𝘦 𝘵𝘩𝘦 𝘣𝘶𝘵𝘵𝘰𝘯𝘴 𝘰𝘳 /start.")

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
        await update.message.reply_text(f"🖼️ 𝘗𝘩𝘰𝘵𝘰 𝘴𝘦𝘯𝘵 𝘵𝘰 {count} 𝘶𝘴𝘦𝘳𝘴.")
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
        await update.message.reply_text(f"🎥 𝘝𝘪𝘥𝘦𝘰 𝘴𝘦𝘯𝘵 𝘵𝘰 {count} 𝘶𝘴𝘦𝘳𝘴.")
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
        await update.message.reply_text(f"🎵 𝘈𝘶𝘥𝘪𝘰 𝘴𝘦𝘯𝘵 𝘵𝘰 {count} 𝘶𝘴𝘦𝘳𝘴.")
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
        await update.message.reply_text(f"📄 𝘋𝘰𝘤𝘶𝘮𝘦𝘯𝘵 𝘴𝘦𝘯𝘵 𝘵𝘰 {count} 𝘶𝘴𝘦𝘳𝘴.")
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
            await update.message.reply_text(f"🎞️ 𝘎𝘐𝘍 𝘴𝘦𝘯𝘵 𝘵𝘰 {count} 𝘶𝘴𝘦𝘳𝘴.")
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
            await update.message.reply_text(f"🎞️ 𝘎𝘐𝘍 (𝘢𝘴 𝘥𝘰𝘤𝘶𝘮𝘦𝘯𝘵) 𝘴𝘦𝘯𝘵 𝘵𝘰 {count} 𝘶𝘴𝘦𝘳𝘴.")
            context.user_data.pop("admin_action")
            return
        else:
            await update.message.reply_text("❌ 𝘗𝘭𝘦𝘢𝘴𝘦 𝘴𝘦𝘯𝘥 𝘢 𝘷𝘢𝘭𝘪𝘥 𝘎𝘐𝘍 𝘧𝘪𝘭𝘦.")
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
    application.add_handler(CallbackQueryHandler(owner_menu_callback, pattern="admin_.*"))
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
