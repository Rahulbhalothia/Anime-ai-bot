import asyncio

asyncio.set_event_loop(asyncio.new_event_loop())

import os
import json
import re
import cv2
import requests
import traceback

from pyrogram import Client, filters

# =========================
# CONFIG
# =========================

API_ID = 34695568

API_HASH = "fafa070d35e6738bd289023532bad03e"

BOT_TOKEN = "8143241425:AAGr39PkhCR67jY8aIrsyMgFOxD2VWk9wEY"

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
# CLEAN NAME
# =========================

def clean_name(name):

    name = name.lower()

    # remove brackets
    name = re.sub(r"\[.*?\]", "", name)

    # remove quality tags
    name = re.sub(r"1080p|720p|480p|360p", "", name)

    # remove extensions
    name = re.sub(r"mkv|mp4|x264|aac", "", name)

    # remove episode text
    name = re.sub(r"episode\s*\d+", "", name)

    # remove random numbers
    name = re.sub(r"\d+", "", name)

    # remove symbols
    name = re.sub(r"[^a-zA-Z ]", "", name)

    return (
        name.replace(" ", "")
        .strip()
    )

# =========================
# TRACE.MOE AI DETECTION
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

        if confidence < 0.80:
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
# SAVE FORWARDED ANIME
# =========================

@app.on_message(filters.video | filters.document)
async def save_episode(client, message):

    try:

        print("Downloading video...")

        # DOWNLOAD VIDEO
        video_path = await message.download()

        print("Extracting frame...")

        # EXTRACT FRAME
        frame = extract_frame(video_path)

        if not frame:

            await message.reply_text(
                "❌ Frame extraction failed"
            )

            return

        print("Detecting anime...")

        # AI DETECTION
        detected = detect_anime(frame)

        if not detected:

            await message.reply_text(
                "❌ Anime not detected"
            )

            return

        anime_name = clean_name(detected)

        print(f"Clean Name: {anime_name}")

        # CREATE ENTRY
        if anime_name not in anime_db:
            anime_db[anime_name] = []

        # SAVE MESSAGE ID
        msg_id = message.id

        anime_db[anime_name].append(msg_id)

        save_db()

        await message.reply_text(
            f"✅ Saved: {anime_name}"
        )

        print(f"Saved {anime_name}")

    except Exception:

        print("SAVE ERROR:")
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
🎬  ANIME LISTING BOT  🎬
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
                photo="https://files.catbox.moe/7w1l6a.jpg",
                caption=welcome_text
            )

            return

        # =========================
        # SEARCH ANIME
        # =========================

        anime = clean_name(args[1])

        found_anime = None

        # PARTIAL SEARCH
        for saved_name in anime_db:

            if anime in saved_name:

                found_anime = saved_name
                break

        if not found_anime:

            await message.reply_text(
                "❌ Anime not found"
            )

            return

        ids = anime_db[found_anime]

        await message.reply_text(
            f"🔥 Found {len(ids)} episodes of {anime}"
        )

        # SEND EPISODES
        for msg_id in ids:

            try:

                await client.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=message.chat.id,
                    message_id=msg_id
                )

            except Exception:

                traceback.print_exc()

    except Exception:

        print("START ERROR:")
        traceback.print_exc()

# =========================
# RUN
# =========================

try:

    print("🔥 AI Anime Bot Running")

    app.run()

except Exception:

    print("BOT ERROR:")
    traceback.print_exc()
