from pyrogram import Client, filters
import requests
import os
import json
import cv2
import re

# =========================
# CONFIG
# =========================

API_ID = 34695568
API_HASH = "fafa070d35e6738bd289023532bad03e"

BOT_TOKEN = "YOUR_BOT_TOKEN"

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

    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"[^a-zA-Z0-9 ]", "", name)

    return (
        name.lower()
        .replace(" ", "")
        .strip()
    )

# =========================
# TRACE.MOE AI DETECTION
# =========================

def detect_anime(image_path):

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

# =========================
# EXTRACT VIDEO FRAME
# =========================

def extract_frame(video_path, output="frame.jpg"):

    cap = cv2.VideoCapture(video_path)

    success, frame = cap.read()

    if success:
        cv2.imwrite(output, frame)

    cap.release()

    return output

# =========================
# SAVE FORWARDED ANIME
# =========================

@app.on_message(filters.video | filters.document)
async def save_episode(client, message):

    try:

        caption = message.caption or ""

        # DOWNLOAD VIDEO
        video_path = await message.download()

        # EXTRACT FRAME
        frame = extract_frame(video_path)

        # AI DETECTION
        detected = detect_anime(frame)

        if not detected:

            await message.reply_text(
                "❌ Anime not detected"
            )

            return

        anime_name = clean_name(detected)

        # CREATE ENTRY
        if anime_name not in anime_db:
            anime_db[anime_name] = []

        anime_db[anime_name].append(message.id)

        save_db()

        await message.reply_text(
            f"✅ Saved: {anime_name}"
        )

        print(f"Saved {anime_name}")

    except Exception as e:

        print(e)

# =========================
# START COMMAND
# =========================

@app.on_message(filters.command("start"))
async def start(client, message):

    args = message.text.split()

    if len(args) < 2:

        await message.reply_text(
            "🎬 Send anime from website"
        )

        return

    anime = clean_name(args[1])

    if anime not in anime_db:

        await message.reply_text(
            "❌ Anime not found"
        )

        return

    ids = anime_db[anime]

    await message.reply_text(
        f"🔥 {anime.upper()} Episodes Found"
    )

    for msg_id in ids:

        await client.copy_message(
            chat_id=message.chat.id,
            from_chat_id=message.chat.id,
            message_id=msg_id
        )

# =========================
# RUN
# =========================

print("🔥 AI Anime Bot Running")

app.run()
