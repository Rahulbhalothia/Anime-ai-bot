import os
import re
import json
import difflib
import traceback
import asyncio
import random
import requests

import requests

from dotenv import load_dotenv
load_dotenv()

from pyrogram import Client, filters
from pyrogram.enums import ChatAction
# =========================================
# VARIABLES
# =========================================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# YOUR TELEGRAM USER ID
ADMIN_ID = 6270115110

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
# CLEAN NAME
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
# MEMORY
# =========================================

chat_memory = {}

# =========================================
# SAVE MODE
# =========================================

save_mode = {}

# =========================================
# SEND MODE
# =========================================

send_mode = {}

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
- funny
- emotional
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

🌸 Hey {message.from_user.first_name} ~

I'm Rei 😎
Ultra Smart Anime AI

━━━━━━━━━━━━━━━

🤖 AI Chat
🎬 Anime Sending
💕 Emotional Support
🎮 Anime Recommendations
💻 Coding Help

━━━━━━━━━━━━━━━

📦 USER COMMANDS

🎬 /send anime_name
→ Anime episodes bhejega

🛑 /stop
→ Anime sending pause karega

▶ /continue
→ Anime wahi se continue karega

━━━━━━━━━━━━━━━

📥 ADMIN COMMANDS

📦 /batch anime_name
→ Saving mode ON

🛑 /stopbatch
→ Saving mode OFF

━━━━━━━━━━━━━━━

✨ Examples:

• /send Naruto
• hello rei
• mood off

"""

    await message.reply_text(text)

# =========================================
# BATCH START
# =========================================

@app.on_message(filters.command("batch"))
async def batch_start(client, message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        anime_name = message.text.split(None, 1)[1]

    except:

        return await message.reply_text(
            "❌ Usage:\n/batch Naruto"
        )

    anime_name = clean_name(anime_name)

    save_mode[message.chat.id] = anime_name

    if anime_name not in anime_db:

        anime_db[anime_name] = []

    await message.reply_text(

        f"""
🔥 Saving Mode ON

🎬 Anime:
{anime_name.title()}

📥 Ab episodes/videos forward karo.

🛑 Stop:
 /stopbatch
"""

    )

# =========================================
# STOP BATCH
# =========================================

@app.on_message(filters.command("stopbatch"))
async def stop_batch(client, message):

    if message.from_user.id != ADMIN_ID:
        return

    if message.chat.id not in save_mode:

        return await message.reply_text(
            "❌ No active batch."
        )

    anime = save_mode[message.chat.id]

    del save_mode[message.chat.id]

    save_db()

    await message.reply_text(

        f"""
✅ Saving Mode OFF

🎬 Anime:
{anime.title()}

📦 Anime saved successfully.
"""

    )

# =========================================
# SAVE FORWARDED EPISODES
# =========================================

@app.on_message(
    filters.private
    & (filters.video | filters.document)
)
async def save_episodes(client, message):

    if message.from_user.id != ADMIN_ID:
        return

    if message.chat.id not in save_mode:
        return

    anime_name = save_mode[message.chat.id]

    anime_db[anime_name].append({

        "message_id": message.id,
        "chat_id": message.chat.id

    })

    save_db()

    total = len(anime_db[anime_name])

    await message.reply_text(

        f"""
✅ Episode Saved

🎬 Anime:
{anime_name.title()}

📦 Total Episodes:
{total}
"""

    )

# =========================================
# SEND ANIME
# =========================================

@app.on_message(filters.command("send"))
async def send_anime(client, message):

    try:

        query = message.text.split(None, 1)[1]

    except:

        return await message.reply_text(
            "❌ Usage:\n/send Naruto"
        )

    query = clean_name(query)

    found = None

    # EXACT + PARTIAL
    for anime in anime_db:

        db_name = clean_name(anime)

        if query == db_name or query in db_name:

            found = anime
            break

    # FUZZY
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

    send_mode[message.chat.id] = {

        "anime": found,
        "episodes": episodes,
        "index": 0,
        "stopped": False

    }

    status = await message.reply_text(

        f"""
🔥 Sending Anime

🎬 {found.title()}
📦 Episodes: {len(episodes)}
"""

    )

    while True:

        data = send_mode.get(message.chat.id)

        if not data:
            return

        if data["stopped"]:

            await status.edit_text(
                "🛑 Anime paused."
            )

            return

        if data["index"] >= len(data["episodes"]):

            await status.edit_text(
                "✅ Anime completed."
            )

            del send_mode[message.chat.id]

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
    & ~filters.command([

        "start",
        "batch",
        "stopbatch",
        "send"

    ])
)
async def main_chat(client, message):

    try:

        user_text = message.text.strip()

        if not user_text:
            return

        lower = user_text.lower()

        # =========================================
        # STOP SEND
        # =========================================

        if lower in [

            "stop",
            "/stop",
            "pause",
            "ruk"

        ]:

            if message.chat.id in send_mode:

                send_mode[message.chat.id]["stopped"] = True

                return await message.reply_text(
                    "🛑 Anime paused."
                )

        # =========================================
        # CONTINUE SEND
        # =========================================

        if lower in [

            "continue",
            "/continue",
            "resume",
            "start again"

        ]:

            if message.chat.id not in send_mode:

                return await message.reply_text(
                    "❌ No paused anime."
                )

            if not send_mode[message.chat.id]["stopped"]:

                return await message.reply_text(
                    "⚡ Already running."
                )

            send_mode[message.chat.id]["stopped"] = False

            await message.reply_text(
                "▶ Continuing anime..."
            )

            while True:

                data = send_mode.get(message.chat.id)

                if not data:
                    return

                if data["stopped"]:
                    return

                if data["index"] >= len(data["episodes"]):

                    await message.reply_text(
                        "✅ Anime completed."
                    )

                    del send_mode[message.chat.id]

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
