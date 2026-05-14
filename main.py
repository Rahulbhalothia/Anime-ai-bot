# =========================================
# 🌸 REI ULTRA SMART AI ANIME BOT
# =========================================

import os
import re
import io
import json
import asyncio
import traceback
import difflib
import random

from pyrogram import Client, filters
from pyrogram.enums import ChatAction

import google.generativeai as genai
from PIL import Image

# =========================================
# ⚙️ VARIABLES
# =========================================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 👑 YOUR IDS
ADMIN_ID = 6270115110
CHANNEL_ID = -1002140125432

DB_FILE = "anime_db.json"

# =========================================
# 🤖 GEMINI SETUP
# =========================================

genai.configure(
    api_key=GEMINI_API_KEY
)

model = genai.GenerativeModel(
    "gemini-2.0-flash"
)

# =========================================
# 🚀 BOT
# =========================================

app = Client(
    "rei_ultra_ai",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# =========================================
# 📦 LOAD DATABASE
# =========================================

if os.path.exists(DB_FILE):

    with open(DB_FILE, "r", encoding="utf-8") as f:

        try:

            anime_db = json.load(f)

            if not isinstance(anime_db, dict):
                anime_db = {}

        except:

            anime_db = {}

else:

    anime_db = {}

# =========================================
# 💾 SAVE DATABASE
# =========================================

def save_db():

    with open(DB_FILE, "w", encoding="utf-8") as f:

        json.dump(
            anime_db,
            f,
            indent=4,
            ensure_ascii=False
        )

# =========================================
# 🧠 MEMORY
# =========================================

chat_memory = {}

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

    text = re.sub(
        r"[^a-zA-Z0-9 ]",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()

# =========================================
# 🖼️ AI IMAGE DETECTION
# =========================================

async def detect_anime(client, message):

    try:

        file_data = await client.download_media(
            message,
            in_memory=True
        )

        image = Image.open(
            io.BytesIO(file_data.getbuffer())
        )

        prompt = """
Look at this anime image.

Identify anime name.

Reply ONLY anime title.

No extra text.
"""

        response = model.generate_content(
            [prompt, image]
        )

        anime_name = clean_name(
            response.text
        )

        return anime_name

    except Exception as e:

        print("VISION ERROR:", e)

        return None

# =========================================
# 📥 AUTO SAVE SYSTEM
# =========================================

@app.on_message(

    (
        filters.chat(CHANNEL_ID)

        |

        (
            filters.user(ADMIN_ID)
            &
            filters.forwarded
        )
    )

    &

    (
        filters.video
        |
        filters.document
    )

)

async def auto_save(client, message):

    try:

        anime_name = None

        # =========================================
        # AI DETECTION
        # =========================================

        anime_name = await detect_anime(
            client,
            message
        )

        # =========================================
        # FALLBACK FILE NAME
        # =========================================

        if not anime_name:

            file_obj = (
                message.video
                or
                message.document
            )

            file_name = file_obj.file_name or ""

            anime_name = clean_name(
                file_name
            )

        if not anime_name:
            return

        if anime_name not in anime_db:

            anime_db[anime_name] = []

        duplicate = any(

            x["message_id"] == message.id

            for x in anime_db[anime_name]

        )

        if duplicate:
            return

        anime_db[anime_name].append({

            "message_id": message.id,
            "chat_id": message.chat.id

        })

        save_db()

        print(f"✅ SAVED: {anime_name}")

        # ADMIN CONFIRM

        if message.chat.type.name == "PRIVATE":

            await message.reply_text(

                f"✅ Saved\n\n"
                f"🎬 Anime: {anime_name.title()}"

            )

    except Exception as e:

        print(e)

        traceback.print_exc()

# =========================================
# 🌸 START
# =========================================

@app.on_message(
    filters.command("start")
)

async def start(client, message):

    text = f"""
🌸 Hey {message.from_user.first_name}~

I'm Rei 😎
Ultra Smart Anime AI Assistant ✨

━━━━━━━━━━━━━━━

🎬 Anime Search
🤖 Human-like AI Chat
💖 Emotional Support
😂 Funny Replies
🎮 Anime Recommendations
💻 Coding Help
🖼️ AI Anime Detection
📦 Auto Episode System

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
# 💬 MAIN CHAT
# =========================================

@app.on_message(

    filters.private
    &
    filters.text
    &
    ~filters.bot
    &
    ~filters.command(["start"])

)

async def main_chat(client, message):

    try:

        user_text = message.text.strip()

        if not user_text:
            return

        user_id = str(message.from_user.id)

        query = clean_name(user_text)

        found = None

        # =========================================
        # EXACT SEARCH
        # =========================================

        for anime in anime_db:

            if query == clean_name(anime):

                found = anime
                break

        # =========================================
        # PARTIAL SEARCH
        # =========================================

        if not found:

            for anime in anime_db:

                db_name = clean_name(anime)

                if query in db_name or db_name in query:

                    found = anime
                    break

        # =========================================
        # FUZZY SEARCH
        # =========================================

        if not found:

            cleaned = {

                clean_name(k): k

                for k in anime_db.keys()

            }

            matches = difflib.get_close_matches(

                query,
                cleaned.keys(),
                n=1,
                cutoff=0.4

            )

            if matches:

                found = cleaned[matches[0]]

        # =========================================
        # SEND EPISODES
        # =========================================

        if found:

            episodes = anime_db[found]

            status = await message.reply_text(

                f"🔥 {found.title()} mil gaya!\n\n"
                f"📦 Sending Episodes..."

            )

            sent = 0

            for ep in episodes:

                try:

                    await client.copy_message(

                        chat_id=message.chat.id,

                        from_chat_id=ep["chat_id"],

                        message_id=ep["message_id"]

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
        # MEMORY
        # =========================================

        if user_id not in chat_memory:

            chat_memory[user_id] = []

        chat_memory[user_id].append(
            f"User: {user_text}"
        )

        chat_memory[user_id] = chat_memory[user_id][-10:]

        memory_text = "\n".join(
            chat_memory[user_id]
        )

        # =========================================
        # TYPING
        # =========================================

        await client.send_chat_action(
            message.chat.id,
            ChatAction.TYPING
        )

        wait = await message.reply_text(

            random.choice([

                "🌸 Thinking...",
                "💭 Hmm...",
                "✨ Cooking reply...",
                "🤖 Processing...",
                "💕 Typing..."

            ])

        )

        # =========================================
        # AI PROMPT
        # =========================================

        prompt = f"""

You are Rei 🌸

You are:
- human like
- emotional
- funny
- smart
- anime obsessed
- friendly
- stylish

You speak natural Hinglish.

Never robotic.

Keep replies short-medium.

You deeply know:
- anime
- coding
- gaming
- memes
- studies
- emotional support

Conversation:
{memory_text}

User:
{user_text}
"""

        # =========================================
        # AI RESPONSE
        # =========================================

        response = model.generate_content(
            prompt
        )

        try:

            reply = response.text.strip()

        except:

            reply = "🌸 Hmm~ bolo na 💕"

        if not reply:

            reply = "🌸 Hmmm~"

        chat_memory[user_id].append(
            f"Rei: {reply}"
        )

        await wait.edit_text(reply)

    except Exception as e:

        print(e)

        traceback.print_exc()

        await message.reply_text(
            "❌ Error aa gaya..."
        )

# =========================================
# 🚀 RUN
# =========================================

if __name__ == "__main__":

    print("🌸 Rei Ultra Smart AI Running...")

    app.run()
