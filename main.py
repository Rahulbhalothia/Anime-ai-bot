import asyncio

asyncio.set_event_loop(asyncio.new_event_loop())

import os
import json
import re
import cv2
import requests
import traceback
import difflib

from pyrogram import Client, filters

# =========================
# CONFIG
# =========================

API_ID = 34695568

API_HASH = "fafa070d35e6738bd289023532bad03e"

BOT_TOKEN = "8143241425:AAGr39PkhCR67jY8aIrsyMgFOxD2VWk9wEY"

STORAGE_CHANNEL = -1002224266205

DB_FILE = "anime_db.json"

# =========================
# BOT
# =========================

app = Client(
    "AnimeAI",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# =========================
# DATABASE
# =========================

if os.path.exists(DB_FILE):

    with open(DB_FILE, "r") as f:
        anime_db = json.load(f)

else:
    anime_db = {}

def save_db():

    with open(DB_FILE, "w") as f:
        json.dump(anime_db, f, indent=4)

# =========================
# SMART CLEAN NAME
# =========================

def clean_name(name):

    name = str(name).lower()

    remove_words = [
        "1080p", "720p", "480p", "360p",
        "x264", "aac", "mkv", "mp4",
        "hindi", "english", "dual", "audio",
        "bluray", "webrip", "sub", "dub",
        "official"
    ]

    for word in remove_words:
        name = name.replace(word, "")

    name = re.sub(r"episode\\s*\\d+", "", name)
    name = re.sub(r"s\\d+e\\d+", "", name)
    name = re.sub(r"\\d+", "", name)
    name = re.sub(r"[^a-zA-Z ]", "", name)

    return name.replace(" ", "").strip()

# =========================
# TRACE AI DETECTION
# =========================

def detect_anime(image_path):

    try:

        with open(image_path, "rb") as img:

            response = requests.post(
                "https://api.trace.moe/search",
                files={"image": img}
            )

        data = response.json()

        if "result" not in data:
            return None

        if len(data["result"]) == 0:
            return None

        best = data["result"][0]

        anime_name = best.get("filename", "")
        confidence = best.get("similarity", 0)

        print(f"Detected: {anime_name}")
        print(f"Confidence: {confidence}")

        if confidence < 0.75:
            return None

        return anime_name

    except Exception:

        traceback.print_exc()
        return None

# =========================
# EXTRACT VIDEO FRAME
# =========================

def extract_frame(video_path, output="frame.jpg"):

    try:

        cap = cv2.VideoCapture(video_path)

        success, frame = cap.read()

        if success:
            cv2.imwrite(output, frame)

        cap.release()

        return output

    except Exception:

        traceback.print_exc()
        return None

# =========================
# FAST SAVE SYSTEM
# =========================

@app.on_message(filters.reply & filters.text)
async def manual_save(client, message):

    try:

        # REPLIED MESSAGE
        replied = message.reply_to_message

        if not replied:
            return

        # ONLY VIDEO/DOCUMENT
        if not (replied.video or replied.document):
            return

        anime_name = clean_name(message.text)

        if len(anime_name) < 2:

            await message.reply_text(
                "❌ Invalid anime name"
            )

            return

        if anime_name not in anime_db:
            anime_db[anime_name] = []

        # SAVE ORIGINAL MESSAGE ID
        msg_id = (
            replied.forward_from_message_id
            if replied.forward_from_message_id
            else replied.id
        )

        # DUPLICATE PROTECTION
        if msg_id not in anime_db[anime_name]:

            anime_db[anime_name].append(msg_id)

            save_db()

        await message.reply_text(
            f"✅ Saved in {anime_name}"
        )

    except Exception:

        print("SAVE ERROR")
        traceback.print_exc()

# =========================
# SAVE ANIME (OLD AI SYSTEM)
# =========================

@app.on_message(filters.video | filters.document)
async def save_episode(client, message):

    try:

        print("⚡ Fast system active")

    except Exception:

        traceback.print_exc()

# =========================
# START
# =========================

@app.on_message(filters.command("start"))
async def start(client, message):

    try:

        args = message.text.split()

        # =========================
        # WELCOME
        # =========================

        if len(args) < 2:

            text = f"""
✨━━━━━━━━━━━━━━━━━━✨
🎬 ANIME LISTING BOT 🎬
✨━━━━━━━━━━━━━━━━━━✨

🔥 Welcome {message.from_user.first_name}

📥 HOW TO SAVE:

➤ Forward anime episode
➤ Reply anime name

Example:
sololeveling

📥 HOW TO SEARCH:

/start anime_name

✅ Example:
/start sololeveling

⚡ Ultra Fast Anime System
🤖 Smart Anime Search
"""

            await message.reply_photo(
                photo="welcome.png",
                caption=text
            )

            return

        query = clean_name(args[1])

        found = None

        # DIRECT MATCH
        for anime in anime_db:

            if query in anime or anime in query:

                found = anime
                break

        # SIMILAR MATCH
        if not found:

            matches = difflib.get_close_matches(
                query,
                anime_db.keys(),
                n=1,
                cutoff=0.5
            )

            if matches:
                found = matches[0]

        if not found:

            await message.reply_text(
                "❌ Anime not found"
            )

            return

        ids = anime_db[found]

        await message.reply_text(
            f"🔥 Sending {len(ids)} episodes of {found}"
        )

        # FAST SEND
        tasks = []

        for msg_id in ids:

            tasks.append(
                client.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=STORAGE_CHANNEL,
                    message_id=msg_id
                )
            )

        await asyncio.gather(*tasks)

    except Exception:

        print("START ERROR")
        traceback.print_exc()

# =========================
# RUN
# =========================

print("🔥 Ultra Fast Anime Bot Running")

app.run()
