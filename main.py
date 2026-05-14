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
# SAVE DATABASE
# =========================================

def save_db():

    with open(DB_FILE, "w", encoding="utf-8") as f:

        json.dump(anime_db, f, indent=4)

# =========================================
# MEMORY
# =========================================

chat_memory = {}

# =========================================
# BATCH DATA
# =========================================

batch_data = {}

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
# AI CHAT
# =========================================

def ask_ai(user_id, user_text):

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
- emotional
- funny
- smart
- anime girl
- human-like

Reply naturally in Hinglish.

Never sound robotic.

You deeply know:
- anime
- gaming
- coding
- memes
- emotional support

Keep replies stylish and medium size.

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

        if "choices" not in data:

            print(data)

            return "🌸 Rei ka AI brain overload ho gaya 😭"

        reply = data["choices"][0]["message"]["content"]

        chat_memory[user_id].append({

            "role": "assistant",
            "content": reply

        })

        return reply

    except Exception as e:

        print(e)

        return "🌸 AI Error aa gaya 😭"

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
💕 Emotional Support
🎮 Anime Recommendations
💻 Coding Help

━━━━━━━━━━━━━━━

Examples:

• hello rei
• mood off
• best anime
• /batch Naruto

"""

    await message.reply_text(text)

# =========================================
# AUTO SAVE ANIME
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
# BATCH COMMAND
# =========================================

@app.on_message(filters.command("batch"))
async def batch_send(client, message):

    try:

        query = message.text.split(None, 1)[1]

    except:

        return await message.reply_text(
            "Usage:\n/batch Naruto"
        )

    query = clean_name(query)

    found = None

    for anime in anime_db:

        db_name = clean_name(anime)

        if query == db_name or query in db_name:

            found = anime
            break

    if not found:

        cleaned_db = {
            clean_name(k): k
            for k in anime_db.keys()
        }

        matches = difflib.get_close_matches(
            query,
            cleaned_db.keys(),
            n=1,
            cutoff=0.3
        )

        if matches:

            found = cleaned_db[matches[0]]

    if not found:

        return await message.reply_text(
            "❌ Anime not found"
        )

    episodes = anime_db[found]

    batch_data[message.chat.id] = {

        "anime": found,
        "episodes": episodes,
        "index": 0,
        "stopped": False

    }

    status = await message.reply_text(
        f"📦 Sending {found.title()}..."
    )

    while True:

        data = batch_data.get(message.chat.id)

        if not data:
            return

        if data["stopped"]:

            await status.edit_text(
                "🛑 Batch paused."
            )

            return

        if data["index"] >= len(data["episodes"]):

            await status.edit_text(
                "✅ Batch completed."
            )

            del batch_data[message.chat.id]

            return

        ep = data["episodes"][data["index"]]

        try:

            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=ep["chat_id"],
                message_id=ep["message_id"]
            )

        except:
            pass

        data["index"] += 1

        await asyncio.sleep(0.7)

# =========================================
# MAIN CHAT
# =========================================

@app.on_message(
    filters.private
    & filters.text
    & ~filters.bot
    & ~filters.command(["start", "batch"])
)
async def main_chat(client, message):

    try:

        user_text = message.text.strip()

        if not user_text:
            return

        text_lower = user_text.lower()

        # =========================================
        # SMART STOP
        # =========================================

        if text_lower in [

            "stop",
            "pause",
            "ruk",
            "band"

        ]:

            if message.chat.id in batch_data:

                batch_data[message.chat.id]["stopped"] = True

                return await message.reply_text(
                    "🛑 Okay, batch paused."
                )

        # =========================================
        # SMART CONTINUE
        # =========================================

        if text_lower in [

            "continue",
            "resume",
            "start again",
            "chalu"

        ]:

            if message.chat.id not in batch_data:

                return await message.reply_text(
                    "❌ No paused batch."
                )

            if not batch_data[message.chat.id]["stopped"]:

                return await message.reply_text(
                    "⚡ Already running."
                )

            batch_data[message.chat.id]["stopped"] = False

            await message.reply_text(
                "▶ Continuing batch..."
            )

            data = batch_data[message.chat.id]

            while True:

                data = batch_data.get(message.chat.id)

                if not data:
                    return

                if data["stopped"]:
                    return

                if data["index"] >= len(data["episodes"]):

                    await message.reply_text(
                        "✅ Batch completed."
                    )

                    del batch_data[message.chat.id]

                    return

                ep = data["episodes"][data["index"]]

                try:

                    await client.copy_message(
                        chat_id=message.chat.id,
                        from_chat_id=ep["chat_id"],
                        message_id=ep["message_id"]
                    )

                except:
                    pass

                data["index"] += 1

                await asyncio.sleep(0.7)

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

        reply = ask_ai(

            str(message.from_user.id),
            user_text

        )

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
