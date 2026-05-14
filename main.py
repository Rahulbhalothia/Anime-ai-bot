import os
import re
import json
import difflib
import traceback
import asyncio
import random
import requests

from pyrogram import Client, filters
from pyrogram.enums import ChatAction

# =========================================
# VARIABLES
# =========================================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CHANNEL_ID = -1002140125432

DB_FILE = "anime_db.json"

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

if isinstance(anime_db, list):
    anime_db = {}

# =========================================
# MEMORY
# =========================================

chat_memory = {}

# =========================================
# THINKING
# =========================================

thinking_lines = [

    "🌸 Thinking...",
    "✨ Cooking reply...",
    "😎 Rei thinking...",
    "💭 One sec...",
    "💕 Typing..."

]

# =========================================
# SAVE DATABASE
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
# GROQ AI
# =========================================

def ask_ai(user_id, user_text):

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
- anime girl
- smart
- human-like

Reply in short stylish Hinglish.

Never sound robotic.

"""
        }

    ]

    messages.extend(chat_memory[user_id])

    response = requests.post(

        "https://api.groq.com/openai/v1/chat/completions",

        headers={

            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"

        },

        json={

            "model": "llama-3.3-70b-versatile",

            "messages": messages,

            "temperature": 1,

            "max_tokens": 300

        }

    )

    data = response.json()

    print(data)

    if "choices" not in data:

        return "🌸 Rei ka brain overload ho gaya 😭"

    reply = data["choices"][0]["message"]["content"]

    chat_memory[user_id].append({

        "role": "assistant",
        "content": reply

    })

    return reply

# =========================================
# START
# =========================================

@app.on_message(filters.command("start"))
async def start(client, message):

    text = f"""

🌸 Hey {message.from_user.first_name}~

I'm Rei 😎

━━━━━━━━━━━━━━━

🎬 Anime Search
🤖 Smart AI Chat
😂 Funny Replies
💕 Emotional Support
🎮 Anime Recommendations

━━━━━━━━━━━━━━━

Examples:

• Naruto
• Dragon Ball
• Solo Leveling
• hello rei
• mood off

"""

    await message.reply_text(text)

# =========================================
# AUTO INDEX
# =========================================

@app.on_message(
    filters.chat(CHANNEL_ID)
    & (filters.video | filters.document)
)
async def auto_index(client, message):

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

        print(f"Saved: {anime_name}")

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

        found = None

        # EXACT MATCH
        for anime in anime_db:

            if query == clean_name(anime):

                found = anime
                break

        # PARTIAL MATCH
        if not found:

            for anime in anime_db:

                db_name = clean_name(anime)

                if query in db_name or db_name in query:

                    found = anime
                    break

        # FUZZY MATCH
        if not found:

            cleaned_db = {

                clean_name(str(k)): k
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

            ids = anime_db[found]

            status = await message.reply_text(

                f"🔥 {found.title()} mil gaya!\n"
                f"📦 Sending Episodes..."

            )

            sent = 0

            for item in ids:

                try:

                    await client.copy_message(

                        chat_id=message.chat.id,
                        from_chat_id=item["chat_id"],
                        message_id=item["message_id"]

                    )

                    sent += 1

                    await asyncio.sleep(0.5)

                except:
                    pass

            await status.edit_text(

                f"✅ Done\n\n"
                f"📦 Sent: {sent}"

            )

            return

        # =========================================
        # AI CHAT
        # =========================================

        await client.send_chat_action(

            message.chat.id,
            ChatAction.TYPING

        )

        wait = await message.reply_text(
            random.choice(thinking_lines)
        )

        reply = ask_ai(user_id, user_text)

        await wait.edit_text(reply)

    except Exception as e:

        print(e)

        traceback.print_exc()

        await message.reply_text(
            "❌ Error aa gaya..."
        )

# =========================================
# RUN
# =========================================

if __name__ == "__main__":

    print("🌸 Rei Ultra AI Running...")

    app.run()
