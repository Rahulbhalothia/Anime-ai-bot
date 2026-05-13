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

    # remove episode text
    name = re.sub(r"episode\s*\d+", "", name)

    # remove season text
    name = re.sub(r"season\s*\d+", "", name)

    # remove S01E01 style
    name = re.sub(r"s\d+e\d+", "", name)

    # remove brackets
    name = re.sub(r"\[.*?\]", "", name)

    # remove numbers
    name = re.sub(r"\d+", "", name)

    # remove symbols
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
                files={"image": img},
                timeout=30
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

        if confidence < 0.70:
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
# SAVE ANIME
# =========================

@app.on_message(filters.video | filters.document)
async def save_episode(client, message):

    try:

        await message.reply_text("🔍 Detecting anime...")

        # DOWNLOAD VIDEO
        video_path = await message.download()

        # EXTRACT FRAME
        frame = extract_frame(video_path)

        detected = None

        # AI DETECTION
        if frame:
            detected = detect_anime(frame)

        # FALLBACK TO CAPTION
        if not detected:

            caption = message.caption or ""

            detected = caption

        if not detected:

            await message.reply_text(
                "❌ Anime not detected"
            )

            return

        anime_name = clean_name(detected)

        print("FINAL NAME:", anime_name)

        if len(anime_name) < 3:

            await message.reply_text(
                "❌ Anime name too short"
            )

            return

        # CREATE ENTRY
        if anime_name not in anime_db:
            anime_db[anime_name] = []

        msg_id = message.id

        # AVOID DUPLICATES
        if msg_id not in anime_db[anime_name]:
            anime_db[anime_name].append(msg_id)

        save_db()

        await message.reply_text(
            f"✅ Saved: {anime_name}"
        )

    except Exception:

        print("SAVE ERROR")
        traceback.print_exc()

# =========================
# START COMMAND
# =========================

@app.on_message(filters.command("start"))
async def start(client, message):

    try:

        args = message.text.split()

        # =========================
        # WELCOME MESSAGE
        # =========================

        if len(args) < 2:

            welcome_text = f"""
✨━━━━━━━━━━━━━━━━━━✨
🎬 ANIME LISTING BOT 🎬
✨━━━━━━━━━━━━━━━━━━✨

🔥 Welcome {message.from_user.first_name} !!

📥 Send:
/start anime_name

✅ Example:
/start sololeveling

🎞 Bot will send all saved episodes automatically.

⚡ Powered By AI Anime System
"""

            await message.reply_photo(
                photo="https://i.imgur.com/8Km9tLL.jpeg",
                caption=welcome_text
            )

            return

        # =========================
        # SEARCH ANIME
        # =========================

        query = clean_name(args[1])

        print("USER SEARCH:", query)

        found = None

        # DIRECT SEARCH
        for anime in anime_db:

            cleaned_saved = clean_name(anime)

            # both side match
            if query in cleaned_saved or cleaned_saved in query:

                found = anime
                break

        # SIMILAR SEARCH
        if not found:

            matches = difflib.get_close_matches(
                query,
                anime_db.keys(),
                n=1,
                cutoff=0.4
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

        # SEND EPISODES
        for msg_id in ids:

            try:

                await client.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=STORAGE_CHANNEL,
                    message_id=msg_id
                )

            except Exception:

                traceback.print_exc()

    except Exception:

        print("START ERROR")
        traceback.print_exc()

# =========================
# RUN
# =========================

print("🔥 AI Anime Bot Running")

app.run()
