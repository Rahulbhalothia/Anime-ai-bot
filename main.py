# =========================================
# 🌸 REI ULTRA AI ANIME CHAT BOT
# =========================================

import os
import re
import json
import difflib
import traceback
import asyncio
import random

from pyrogram import Client, filters
from pyrogram.enums import ChatAction

import google.generativeai as genai

# =========================================
# VARIABLES
# =========================================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DB_FILE = "anime_list.json"

# YOUR CHANNEL ID
CHANNEL_ID = -1002140125432

# =========================================
# GEMINI AI
# =========================================

genai.configure(
    api_key=GEMINI_API_KEY
)

model = genai.GenerativeModel(
    "gemini-1.5-flash-latest"
)

# =========================================
# BOT
# =========================================

app = Client(
    "rei_ultra_ai",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# =========================================
# LOAD DATABASE
# =========================================

if os.path.exists(DB_FILE):

    with open(DB_FILE, "r", encoding="utf-8") as f:

        try:
            anime_db = json.load(f)

        except:
            anime_db = {}

else:
    anime_db = {}

# FIX DATABASE
if isinstance(anime_db, list):
    anime_db = {}

# =========================================
# MEMORY
# =========================================

chat_memory = {}

# =========================================
# THINKING LINES
# =========================================

thinking_lines = [
    "🌸 Thinking...",
    "✨ Cooking reply...",
    "😎 Rei thinking...",
    "💭 One sec...",
    "🤖 Processing...",
    "💕 Typing...",
    "⚡ Brain loading..."
]

# =========================================
# SAVE DB
# =========================================

def save_db():

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(anime_db, f, indent=4)

# =========================================
# CLEAN NAME
# =========================================

def clean_name(name):

    name = str(name).lower()

    remove_words = [
        "1080p",
        "720p",
        "480p",
        "360p",
        "x264",
        "aac",
        "mkv",
        "mp4",
        "dual",
        "audio",
        "bluray",
        "webrip",
        "episode",
        "ep",
        "season"
    ]

    for word in remove_words:
        name = name.replace(word, " ")

    name = re.sub(r"[^a-zA-Z0-9 ]", "", name)
    name = re.sub(r"\s+", " ", name)

    return name.strip()

# =========================================
# START
# =========================================

@app.on_message(filters.command("start"))
async def start(client, message):

    text = f"""
🌸 Hey {message.from_user.first_name}~

I'm Rei 😎
Ultra AI Anime Assistant ✨

━━━━━━━━━━━━━━━

🎬 Anime Search
🤖 AI Chat
💻 Coding Help
😂 Funny Replies
😭 Emotional Support
🎮 Anime Recommendations
🔥 Smart Anime Detection

━━━━━━━━━━━━━━━

Examples:
• Naruto
• Solo Leveling
• hello rei
• best anime
• mood off
"""

    await message.reply_text(text)

# =========================================
# AUTO CHANNEL INDEX
# =========================================

@app.on_message(
    filters.chat(CHANNEL_ID)
    & (filters.video | filters.document)
)
async def auto_index(client, message):

    try:

        file_name = ""

        # VIDEO
        if message.video:
            file_name = message.video.file_name or ""

        # DOCUMENT
        elif message.document:
            file_name = message.document.file_name or ""

        # CAPTION
        caption = message.caption or ""

        # COMBINE
        combined = f"{file_name} {caption}"

        anime_name = clean_name(combined)

        if len(anime_name) < 2:
            return

        if anime_name not in anime_db:
            anime_db[anime_name] = []

        anime_db[anime_name].append({

            "message_id": message.id,
            "chat_id": message.chat.id

        })

        save_db()

        print(f"✅ Saved: {anime_name}")

    except Exception as e:

        print(e)

# =========================================
# MAIN SYSTEM
# =========================================

@app.on_message(
    filters.text
    & filters.private
    & ~filters.bot
    & ~filters.command(["start"])
)
async def main_system(client, message):

    try:

        user_text = message.text.strip()

        if not user_text:
            return

        user_id = str(message.from_user.id)

        query = clean_name(user_text)

        # =========================================
        # SEARCH ANIME
        # =========================================

        found = None

        # exact
        for anime in anime_db:

            db_name = clean_name(anime)

            if query == db_name:
                found = anime
                break

        # partial
        if not found:

            for anime in anime_db:

                db_name = clean_name(anime)

                if query in db_name or db_name in query:
                    found = anime
                    break

        # fuzzy
        if not found:

            cleaned_db = {
                clean_name(str(k)): k
                for k in anime_db
            }

            matches = difflib.get_close_matches(
                query,
                cleaned_db.keys(),
                n=1,
                cutoff=0.2
            )

            if matches:
                found = cleaned_db[matches[0]]

        # =========================================
        # SEND ANIME
        # =========================================

        if found:

            ids = anime_db[found]

            await client.send_chat_action(
                message.chat.id,
                ChatAction.TYPING
            )

            status = await message.reply_text(
                f"🔥 {found.title()} mil gaya!\n"
                f"📦 Sending {len(ids)} episodes..."
            )

            success = 0
            failed = 0

            used = set()

            for item in ids:

                try:

                    key = (
                        item.get("message_id"),
                        item.get("chat_id")
                    )

                    if key in used:
                        continue

                    used.add(key)

                    await client.copy_message(
                        chat_id=message.chat.id,
                        from_chat_id=item["chat_id"],
                        message_id=item["message_id"]
                    )

                    success += 1

                    if success % 5 == 0:

                        try:

                            await status.edit_text(
                                f"📦 Sending Episodes...\n\n"
                                f"✅ Sent: {success}\n"
                                f"❌ Failed: {failed}"
                            )

                        except:
                            pass

                    await asyncio.sleep(0.7)

                except Exception as e:

                    print(e)

                    failed += 1

            await status.edit_text(
                f"✨ Done Sending\n\n"
                f"✅ Sent: {success}\n"
                f"❌ Failed: {failed}"
            )

            return

        # =========================================
        # AI CHAT
        # =========================================

        if user_id not in chat_memory:
            chat_memory[user_id] = []

        chat_memory[user_id].append({
            "role": "user",
            "content": user_text
        })

        # LIMIT MEMORY
        chat_memory[user_id] = chat_memory[user_id][-20:]

        await client.send_chat_action(
            message.chat.id,
            ChatAction.TYPING
        )

        wait = await message.reply_text(
            random.choice(thinking_lines)
        )

        # =========================================
        # PROMPT
        # =========================================

        prompt = f"""

You are Rei 🌸

You are an ultra smart anime AI assistant.

You are:
- Friendly
- Funny
- Emotional
- Human-like
- Casual
- Smart

You LOVE anime deeply.

You know:
- Naruto
- One Piece
- Solo Leveling
- Dragon Ball
- Jujutsu Kaisen
- Demon Slayer
- Attack On Titan
- Tokyo Ghoul
- Bleach
- All popular anime

You also know:
- coding
- gaming
- memes
- studies
- life

Speaking style:
- natural
- human-like
- casual
- stylish
- use emojis naturally

Never sound robotic.

Conversation:
{chat_memory[user_id]}

User:
{user_text}

"""

        # =========================================
        # GEMINI RESPONSE
        # =========================================

        response = model.generate_content(prompt)

        try:
            reply = response.text
        except:
            reply = "🌸 Rei is sleepy right now~ try again 😭"

        # SAVE MEMORY
        chat_memory[user_id].append({
            "role": "assistant",
            "content": reply
        })

        await wait.edit_text(reply)

    except Exception as e:

        print(e)

        traceback.print_exc()

        await message.reply_text(
            "❌ Something went wrong..."
        )

# =========================================
# RUN
# =========================================

if __name__ == "__main__":

    print("🌸 Rei Ultra AI Running...")

    app.run()
