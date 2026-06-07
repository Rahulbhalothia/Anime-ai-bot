import os
import re
import difflib
import traceback
import asyncio
import random
import time
import requests

from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from pyrogram.errors import FloodWait, MessageNotModified

# =========================================
# ENV VARIABLES
# =========================================

API_ID          = int(os.getenv("API_ID"))
API_HASH        = os.getenv("API_HASH")
BOT_TOKEN       = os.getenv("BOT_TOKEN")
GROQ_API_KEY    = os.getenv("GROQ_API_KEY")
MONGO_URI       = os.getenv("MONGO_URI")
SESSION_STRING  = os.getenv("SESSION_STRING", "")

ADMIN_ID  = 6270115110

# =========================================
# MONGODB SETUP
# =========================================

mongo_client   = MongoClient(MONGO_URI)
db             = mongo_client["anime_bot"]
anime_col      = db["anime"]
users_col      = db["users"]

# =========================================
# BOT CLIENT (session string for Railway)
# =========================================

if SESSION_STRING:
    app = Client(
        "rei_ultra_ai",
        session_string=SESSION_STRING,
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
else:
    # Local run ke liye (file session)
    app = Client(
        "rei_ultra_ai",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )

# =========================================
# IN-MEMORY STATE
# =========================================

anime_db     = {}   # {anime_name: [episodes]}
save_mode    = {}   # {chat_id: {"name": str, "count": int}}
send_mode    = {}   # {chat_id: {anime, episodes, index, stopped, task}}
chat_memory  = {}   # {user_id: [messages]}
rate_limit   = {}   # {user_id: last_message_time}
user_set     = set()  # tracked user ids

RATE_LIMIT_SECS = 1.5  # seconds between messages per user

# =========================================
# THINKING LINES
# =========================================

thinking_lines = [
    "🌸 Thinking...", "✨ Cooking reply...",
    "😎 Rei thinking...", "💭 One sec...",
    "💕 Typing...", "🎀 Processing...",
    "🌙 Almost there...", "⚡ Loading brain..."
]

# =========================================
# DB: LOAD
# =========================================

def load_db():
    global anime_db
    try:
        anime_db = {}
        for doc in anime_col.find():
            anime_db[doc["name"]] = doc["episodes"]
        print(f"✅ DB Loaded: {len(anime_db)} anime")
    except Exception as e:
        print("Mongo Load Error:", e)
        anime_db = {}

load_db()

# =========================================
# DB: SAVE (upsert only changed anime)
# =========================================

def save_db(anime_name=None):
    """Save one anime or all."""
    try:
        targets = {anime_name: anime_db[anime_name]} if anime_name else anime_db
        for name, eps in targets.items():
            anime_col.update_one(
                {"name": name},
                {"$set": {"name": name, "episodes": eps}},
                upsert=True
            )
    except Exception as e:
        print("Mongo Save Error:", e)

# =========================================
# DB: REGISTER USER
# =========================================

def register_user(user):
    uid = user.id
    if uid not in user_set:
        user_set.add(uid)
        users_col.update_one(
            {"user_id": uid},
            {"$set": {
                "user_id": uid,
                "name": user.first_name,
                "username": user.username or ""
            }},
            upsert=True
        )

# =========================================
# UTIL: CLEAN NAME
# =========================================

def clean_name(text):
    text = str(text).lower()
    noise = [
        "1080p","720p","480p","360p","x264","x265","hevc",
        "aac","mkv","mp4","dual","audio","bluray","webrip",
        "episode","ep","season","eng","hindi","dubbed",
        "subbed","batch","hdrip","bdrip","hd","uhd"
    ]
    for w in noise:
        text = re.sub(r'\b' + w + r'\b', ' ', text)
    text = re.sub(r"[^a-zA-Z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# =========================================
# UTIL: FIND ANIME
# =========================================

def find_anime(query):
    query = clean_name(query)
    # exact / substring
    for anime in anime_db:
        db_n = clean_name(anime)
        if query == db_n or query in db_n:
            return anime
    # fuzzy
    cleaned_map = {clean_name(k): k for k in anime_db}
    matches = difflib.get_close_matches(query, cleaned_map.keys(), n=1, cutoff=0.3)
    if matches:
        return cleaned_map[matches[0]]
    return None

# =========================================
# UTIL: RATE LIMIT CHECK
# =========================================

def is_rate_limited(user_id):
    now = time.time()
    last = rate_limit.get(user_id, 0)
    if now - last < RATE_LIMIT_SECS:
        return True
    rate_limit[user_id] = now
    return False

# =========================================
# UTIL: SAFE SEND (handles FloodWait)
# =========================================

async def safe_copy(client, chat_id, from_chat_id, message_id, retries=3):
    for attempt in range(retries):
        try:
            await client.copy_message(
                chat_id=chat_id,
                from_chat_id=from_chat_id,
                message_id=message_id
            )
            return True
        except FloodWait as fw:
            await asyncio.sleep(fw.value + 1)
        except Exception as e:
            print(f"Copy error (attempt {attempt+1}): {e}")
            await asyncio.sleep(1)
    return False

# =========================================
# GROQ AI CALL
# =========================================

def _call_groq(messages, max_tokens=350):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 1,
                "max_tokens": max_tokens
            },
            timeout=20
        )
        data = r.json()
        if "choices" not in data:
            print("Groq Error:", data)
            return None
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("Groq call error:", e)
        return None

REI_SYSTEM = (
    "You are Rei 🌸 — a cute, funny, emotional, super smart anime girl bot on Telegram.\n"
    "Reply naturally in Hinglish (mix of Hindi + English). Use emojis naturally.\n"
    "Never sound robotic. You deeply know: anime, gaming, coding, memes, emotional support.\n"
    "If someone is sad, be extra caring. If someone is happy, vibe with them.\n"
    "If someone asks for anime recommendation, give 2-3 with a reason.\n"
    "Keep replies stylish and medium size (2-6 lines max). Never give walls of text."
)

async def ask_ai_async(user_id, user_text):
    try:
        if user_id not in chat_memory:
            chat_memory[user_id] = []
        chat_memory[user_id].append({"role": "user", "content": user_text})
        chat_memory[user_id] = chat_memory[user_id][-14:]
        messages = [{"role": "system", "content": REI_SYSTEM}] + chat_memory[user_id]
        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(None, lambda: _call_groq(messages))
        if reply:
            chat_memory[user_id].append({"role": "assistant", "content": reply})
            return reply
        return "🌸 Rei ka AI brain overload ho gaya, thoda baad try karo 😭"
    except Exception as e:
        print("AI Error:", e)
        return "🌸 AI Error aa gaya 😭"

async def generate_welcome(first_name):
    try:
        msgs = [
            {"role": "system", "content": (
                "You are Rei 🌸, an Ultra Smart Anime AI bot on Telegram.\n"
                "Generate a warm, hype, fun Hinglish welcome for a new user. Include their name.\n"
                "Use emojis. Keep it 3-4 lines max. NO command list — just the greeting."
            )},
            {"role": "user", "content": f"User ka naam: {first_name}. Usse welcome karo!"}
        ]
        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(None, lambda: _call_groq(msgs, max_tokens=120))
        return reply or f"🌸 Hey {first_name} ~ Welcome to Rei! 😎"
    except Exception:
        return f"🌸 Hey {first_name} ~ Welcome to Rei! 😎"

# =========================================
# SEND LOOP (background task)
# =========================================

async def _send_loop(client, chat_id, status_msg):
    try:
        while True:
            data = send_mode.get(chat_id)
            if not data:
                return

            if data["stopped"]:
                try:
                    await status_msg.edit_text(
                        f"🛑 Paused at Episode {data['index']}\n"
                        f"🎬 {data['anime'].title()}\n"
                        f"▶ Resume: /continue"
                    )
                except MessageNotModified:
                    pass
                return

            if data["index"] >= len(data["episodes"]):
                try:
                    await status_msg.edit_text(
                        f"✅ Anime Complete! 🎉\n"
                        f"🎬 {data['anime'].title()}\n"
                        f"📦 All {len(data['episodes'])} episodes sent!"
                    )
                except MessageNotModified:
                    pass
                send_mode.pop(chat_id, None)
                return

            ep = data["episodes"][data["index"]]
            await safe_copy(client, chat_id, ep["chat_id"], ep["message_id"])
            data["index"] += 1
            await asyncio.sleep(0.5)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print("Send loop error:", e)

# =========================================
# /start
# =========================================

@app.on_message(filters.command("start"))
async def cmd_start(client, message):
    register_user(message.from_user)
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    ai_welcome = await generate_welcome(message.from_user.first_name)

    info = (
        "\n━━━━━━━━━━━━━━━\n\n"
        "🤖 AI Chat\n🎬 Anime Sending\n💕 Emotional Support\n"
        "🎮 Anime Recommendations\n💻 Coding Help\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        "📦 USER COMMANDS\n\n"
        "🎬 /send anime_name — Episodes bhejega\n"
        "🔍 /search query — Anime search karo\n"
        "📋 /list — Sabhi anime dekho\n"
        "📊 /status — Current sending status\n"
        "⏩ /ep anime_name 5 — Specific episode se start\n"
        "🛑 /stop — Pause karo\n"
        "▶ /continue — Resume karo\n"
        "🧹 /clear — Chat memory reset\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        "✨ Examples:\n"
        "- /send Naruto\n- /ep One Piece 50\n- /search attack on titan\n- mood off"
    )
    await message.reply_text(ai_welcome + info)

# =========================================
# /list — show all anime
# =========================================

@app.on_message(filters.command("list"))
async def cmd_list(client, message):
    if not anime_db:
        return await message.reply_text("📭 Database empty hai abhi.")

    lines = [f"📚 Total Anime: {len(anime_db)}\n━━━━━━━━━━━━━━━"]
    for i, (name, eps) in enumerate(sorted(anime_db.items()), 1):
        lines.append(f"{i}. {name.title()} — {len(eps)} eps")

    # Split if too long
    text = "\n".join(lines)
    if len(text) > 4000:
        chunks = []
        chunk = ""
        for line in lines:
            if len(chunk) + len(line) > 3800:
                chunks.append(chunk)
                chunk = ""
            chunk += line + "\n"
        if chunk:
            chunks.append(chunk)
        for c in chunks:
            await message.reply_text(c)
    else:
        await message.reply_text(text)

# =========================================
# /search — find anime
# =========================================

@app.on_message(filters.command("search"))
async def cmd_search(client, message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return await message.reply_text("❌ Usage: /search Naruto")

    query = clean_name(parts[1])
    results = []

    for anime in anime_db:
        db_n = clean_name(anime)
        if query in db_n:
            results.append(anime)

    # fuzzy top 5
    if not results:
        cleaned_map = {clean_name(k): k for k in anime_db}
        matches = difflib.get_close_matches(query, cleaned_map.keys(), n=5, cutoff=0.3)
        results = [cleaned_map[m] for m in matches]

    if not results:
        return await message.reply_text(
            f"❌ '{parts[1]}' nahi mila.\n💡 /list se sabhi anime dekho."
        )

    lines = [f"🔍 Search: '{parts[1]}'\n━━━━━━━━━━━━━━━"]
    for i, name in enumerate(results[:10], 1):
        lines.append(f"{i}. {name.title()} — {len(anime_db[name])} eps")

    await message.reply_text("\n".join(lines))

# =========================================
# /status — what's currently sending
# =========================================

@app.on_message(filters.command("status"))
async def cmd_status(client, message):
    data = send_mode.get(message.chat.id)
    if not data:
        return await message.reply_text("📭 Koi anime chal nahi raha.")

    state = "🛑 Paused" if data["stopped"] else "▶ Running"
    pct = int((data["index"] / max(len(data["episodes"]), 1)) * 100)
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)

    await message.reply_text(
        f"📊 STATUS\n━━━━━━━━━━━━━━━\n"
        f"🎬 Anime: {data['anime'].title()}\n"
        f"📦 Progress: {data['index']}/{len(data['episodes'])}\n"
        f"[{bar}] {pct}%\n"
        f"⚡ State: {state}"
    )

# =========================================
# /ep — send from specific episode
# =========================================

@app.on_message(filters.command("ep"))
async def cmd_ep(client, message):
    parts = message.text.split()
    # /ep Naruto 25  or  /ep One Piece 50
    if len(parts) < 3:
        return await message.reply_text(
            "❌ Usage:\n/ep Naruto 25\n/ep One Piece 50"
        )

    try:
        ep_num = int(parts[-1])
        anime_query = " ".join(parts[1:-1])
    except ValueError:
        return await message.reply_text("❌ Last argument episode number hona chahiye.\nExample: /ep Naruto 25")

    found = find_anime(anime_query)
    if not found:
        return await message.reply_text(f"❌ '{anime_query}' nahi mila.")

    episodes = anime_db[found]
    if ep_num < 1 or ep_num > len(episodes):
        return await message.reply_text(
            f"❌ Episode {ep_num} exist nahi karta.\n"
            f"📦 {found.title()} mein sirf {len(episodes)} episodes hain."
        )

    # Cancel existing
    existing = send_mode.get(message.chat.id)
    if existing and existing.get("task"):
        existing["task"].cancel()

    start_idx = ep_num - 1
    status = await message.reply_text(
        f"⏩ Starting from Episode {ep_num}\n"
        f"🎬 {found.title()}\n"
        f"📦 {len(episodes) - start_idx} episodes remaining\n\n"
        f"🛑 /stop | ▶ /continue"
    )

    send_mode[message.chat.id] = {
        "anime": found,
        "episodes": episodes,
        "index": start_idx,
        "stopped": False,
        "task": None
    }

    task = asyncio.create_task(_send_loop(client, message.chat.id, status))
    send_mode[message.chat.id]["task"] = task

# =========================================
# /send
# =========================================

@app.on_message(filters.command("send"))
async def cmd_send(client, message):
    register_user(message.from_user)
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return await message.reply_text("❌ Usage:\n/send Naruto")

    found = find_anime(parts[1])
    if not found:
        return await message.reply_text(
            f"❌ '{parts[1]}' nahi mila.\n"
            f"🔍 Try /search {parts[1]}\n"
            f"📋 Ya /list se dekho."
        )

    episodes = anime_db[found]
    if not episodes:
        return await message.reply_text(f"❌ {found.title()} ke episodes nahi hain abhi.")

    existing = send_mode.get(message.chat.id)
    if existing and existing.get("task"):
        existing["task"].cancel()

    status = await message.reply_text(
        f"🔥 Sending Anime\n\n"
        f"🎬 {found.title()}\n"
        f"📦 Total Episodes: {len(episodes)}\n\n"
        f"🛑 /stop  |  ▶ /continue  |  📊 /status"
    )

    send_mode[message.chat.id] = {
        "anime": found,
        "episodes": episodes,
        "index": 0,
        "stopped": False,
        "task": None
    }

    task = asyncio.create_task(_send_loop(client, message.chat.id, status))
    send_mode[message.chat.id]["task"] = task

# =========================================
# /stop
# =========================================

@app.on_message(filters.command("stop"))
async def cmd_stop(client, message):
    if message.chat.id in send_mode:
        send_mode[message.chat.id]["stopped"] = True
        data = send_mode[message.chat.id]
        await message.reply_text(
            f"🛑 Anime Paused!\n"
            f"🎬 {data['anime'].title()} — Episode {data['index']}\n"
            f"▶ Resume: /continue"
        )
    else:
        await message.reply_text("❌ Koi anime chal nahi raha.")

# =========================================
# /continue
# =========================================

@app.on_message(filters.command("continue"))
async def cmd_continue(client, message):
    if message.chat.id not in send_mode:
        return await message.reply_text("❌ Koi paused anime nahi hai.")

    data = send_mode[message.chat.id]
    if not data["stopped"]:
        return await message.reply_text("⚡ Anime already chal raha hai!")

    data["stopped"] = False
    status = await message.reply_text(
        f"▶ Resuming...\n"
        f"🎬 {data['anime'].title()}\n"
        f"📦 Episode {data['index'] + 1} se"
    )

    if data.get("task"):
        data["task"].cancel()

    task = asyncio.create_task(_send_loop(client, message.chat.id, status))
    data["task"] = task

# =========================================
# /clear — reset AI memory
# =========================================

@app.on_message(filters.command("clear"))
async def cmd_clear(client, message):
    uid = str(message.from_user.id)
    chat_memory.pop(uid, None)
    await message.reply_text("🧹 Memory cleared!\nAb fresh start karte hain 🌸")

# =========================================
# ADMIN: /batch
# =========================================

@app.on_message(filters.command("batch"))
async def cmd_batch(client, message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply_text("❌ Sirf admin use kar sakta hai.")

    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return await message.reply_text("❌ Usage:\n/batch Naruto")

    anime_name = clean_name(parts[1])
    if not anime_name:
        return await message.reply_text("❌ Valid anime name do.")

    if anime_name not in anime_db:
        anime_db[anime_name] = []

    existing = len(anime_db[anime_name])
    save_mode[message.chat.id] = {"name": anime_name, "count": existing}

    await message.reply_text(
        f"🔥 Saving Mode ON\n\n"
        f"🎬 Anime: {anime_name.title()}\n"
        f"📦 Already saved: {existing} episodes\n\n"
        f"📥 Ab episodes/videos forward karo.\n"
        f"🛑 Stop: /stopbatch"
    )

# =========================================
# ADMIN: /stopbatch
# =========================================

@app.on_message(filters.command("stopbatch"))
async def cmd_stopbatch(clien
