# =========================================
# 🌸 REI ULTRA AI ANIME BOT
# =========================================

import os
import re
import json
import asyncio
import traceback
import difflib
import requests

from pyrogram import Client, filters
from pyrogram.enums import ChatAction

# =========================================
# 🔥 VARIABLES
# =========================================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# OPENROUTER API
OPENROUTER_API_KEY = os.getenv("REI_API_KEY")

# CHANNEL ID
CHANNEL_ID = -1002140125432

DB_FILE = "anime_db.json"

# =========================================
# 🤖 BOT
# =========================================

app = Client(
    "rei_ultra_ai",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# =========================================
# 💾 DATABASE
# =========================================

if os.path.exists(DB_FILE):

    with open(DB_FILE, "r", encoding="utf-8") as f:

        try:
            anime_db = json.load(f)

        except:
            anime_db = {}

else:
    anime_db = {}

if isinstance(anime_db, list):
    anime_db = {}

# =========================================
# 🧠 MEMORY
# =========================================

chat_memory = {}

# =========================================
# 💬 THINKING LINES
# =========================================

thinking_lines = [
    "🌸 Thinking...",
    "✨ Cooking reply...",
    "😎 Rei thinking...",
    "💭 One sec...",
    "🤖 Processing...",
    "💕 Typing..."
]

# =========================================
# 💾 SAVE DATABASE
# =========================================

def save_db():

    with open(DB_FILE, "w", encoding="utf-8") as f:

        json.dump(anime_db, f, indent=4)

# =========================================
# 🧹 CLEAN NAME
# =========================================

def clean_name(text):

    text = str(text).lower()

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
        text = text.replace(word, " ")

    text = re.sub(r"[^a-zA-Z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()

# =========================================
# 🚀 START
# =========================================

@app.on_message(filters.command("start"))
async def start(client, message):

    txt = f"""
🌸 Hey {message.from_user.first_name} ~

I'm Rei 😎

━━━━━━━━━━━━━━━

🎬 Anime Search
🤖 Smart AI Chat
💻 Coding Help
😂 Funny Replies
🎮 Anime Recommendations
💕 Emotional Support

━━━━━━━━━━━━━━━

Examples:
• Naruto
• Dragon Ball
• Solo Leveling
• hello rei
• mood off
"""

    await message.reply_text(txt)

# =========================================
# 📥 AUTO SAVE ANIME
# =========================================

@app.on_message(
    filters.chat(CHANNEL_ID)
    & (filters.video | filters.document)
)
async def auto_save(client, message):

    try:

        file_name = ""

        if message.video:
            file_name = message.video.file_name or ""

        elif message.document:
            file_name = message.document.file_name or ""

        caption = message.caption or ""

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
# 🤖 AI CHAT FUNCTION
# =========================================

def get_ai_reply(user_id, user_text):

    try:

        if user_id not in chat_memory:
            chat_memory[user_id] = []

        chat_memory[user_id].append({

            "role": "user",
            "content": user_text

        })

        chat_memory[user_id] = chat_memory[user_id][-10:]

        messages = [

            {
                "role": "system",
                "content": """

You are Rei 🌸

You are:
- cute
- funny
- emotional
- smart
- anime lover
- human-like

Reply in natural Hinglish.

You love:
- Naruto
- One Piece
- Dragon Ball
- Solo Leveling
- Anime
- Gaming
- Coding
- Memes

Never sound robotic.
Keep replies stylish and short.

"""
            }

        ]

        messages.extend(chat_memory[user_id])

        response = requests.post(

            "https://openrouter.ai/api/v1/chat/completions",

            headers={

                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"

            },

            json={

                "model": "mistralai/mistral-7b-instruct:free",

                "messages": messages

            },

            timeout=60

        )

        data = response.json()

        print(data)

        reply = data["choices"][0]["message"]["content"]

        chat_memory[user_id].append({

            "role": "assistant",
            "content": reply

        })

        return reply

    except Exception as e:

        print(e)

        return "🌸 Rei ka brain lag ho gaya 😭"

# =========================================
# 🎬 MAIN SYSTEM
# =========================================

@app.on_message(
    filters.private
    & filters.text
    & ~filters.bot
    & ~filters.command(["start"])
)
async def main_system(client, message):

    try:

        text = message.text.strip()

        if not text:
            return

        query = clean_name(text)

        found = None

        # EXACT SEARCH
        for anime in anime_db:

            db_name = clean_name(anime)

            if query == db_name:

                found = anime
                break

        # PARTIAL SEARCH
        if not found:

            for anime in anime_db:

                db_name = clean_name(anime)

                if query in db_name or db_name in query:

                    found = anime
                    break

        # FUZZY SEARCH
        if not found:

            cleaned_db = {

                clean_name(k): k
                for k in anime_db

            }

            matches = difflib.get_close_matches(

                query,
                cleaned_db.keys(),
                n=1,
                cutoff=0.3

            )

            if matches:

                found = cleaned_db[matches[0]]

        # =========================================
        # SEND ANIME
        # =========================================

        if found:

            episodes = anime_db[found]

            await message.reply_text(

                f"🔥 {found.title()} mil gaya!\n"
                f"📦 Sending Episodes..."

            )

            for ep in episodes:

                try:

                    await client.copy_message(

                        chat_id=message.chat.id,
                        from_chat_id=ep["chat_id"],
                        message_id=ep["message_id"]

                    )

                    await asyncio.sleep(0.5)

                except:
                    pass

            return

        # =========================================
        # AI CHAT
        # =========================================

        await client.send_chat_action(

            message.chat.id,
            ChatAction.TYPING

        )

        wait = await message.reply_text(

            thinking_lines[0]

        )

        reply = get_ai_reply(

            str(message.from_user.id),
            text

        )

        await wait.edit_text(reply)

    except Exception as e:

        traceback.print_exc()

        await message.reply_text(

            "❌ Error aa gaya..."

        )

# =========================================
# ▶️ RUN
# =========================================

print("🌸 Rei Ultra AI Running...")

app.run()
