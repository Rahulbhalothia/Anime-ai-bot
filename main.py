# =========================================
# 🌸 REI ULTRA PRO MAX AI ANIME BOT
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
from openai import AsyncOpenAI

# =========================================
# VARIABLES
# =========================================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DB_FILE = "anime_list.json"

# =========================================
# OPENAI
# =========================================

ai = AsyncOpenAI(
    api_key=OPENAI_API_KEY
)

# =========================================
# BOT
# =========================================

app = Client(
    "rei_ultra_pro_max",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# =========================================
# DATABASE
# =========================================

if os.path.exists(DB_FILE):

    with open(DB_FILE, "r", encoding="utf-8") as f:
        anime_db = json.load(f)

else:
    anime_db = {}

# =========================================
# MEMORY
# =========================================

chat_memory = {}

# =========================================
# RANDOM STATUS
# =========================================

thinking_lines = [
    "🌸 Thinking...",
    "✨ Cooking a reply...",
    "😎 Rei is thinking...",
    "💭 One sec...",
    "🤖 Processing..."
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
# START
# =========================================

@app.on_message(filters.command("start"))
async def start(client, message):

    text = f"""
🌸 Hey {message.from_user.first_name}~ ✨

I'm Rei 😎
Your Ultra Pro Max AI Anime Assistant 💕

━━━━━━━━━━━━━━━

💬 I can:
🎬 Send anime episodes
🤖 Talk like AI
💖 Chat like a real friend
🎮 Anime recommendations
💻 Coding help
📚 Study help
😂 Fun conversations
😭 Emotional support

━━━━━━━━━━━━━━━

✨ Just type naturally~

Examples:
• Solo Leveling
• hello rei
• best anime
• mood off
"""

    await message.reply_text(text)

# =========================================
# HELP
# =========================================

@app.on_message(filters.command("help"))
async def help_command(client, message):

    text = """
🌸 REI HELP ✨

━━━━━━━━━━━━━━━

🎬 Anime:
• Naruto
• Solo Leveling
• One Piece

━━━━━━━━━━━━━━━

💬 AI Chat:
• hello
• talk to me
• mood off

━━━━━━━━━━━━━━━

💻 Coding:
• python help
• fix error

━━━━━━━━━━━━━━━

⚡ Commands:
/start
/help
/reset
"""

    await message.reply_text(text)

# =========================================
# RESET
# =========================================

@app.on_message(filters.command("reset"))
async def reset_memory(client, message):

    user_id = str(message.from_user.id)

    if user_id in chat_memory:
        del chat_memory[user_id]

    await message.reply_text(
        "🧹 Memory cleared~"
    )

# =========================================
# MAIN SYSTEM
# =========================================

@app.on_message(
    filters.text
    & filters.private
    & ~filters.bot
    & ~filters.command([
        "start",
        "help",
        "reset"
    ])
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
                clean_name(k): k
                for k in anime_db.keys()
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
        # AI CHAT SYSTEM
        # =========================================

        if user_id not in chat_memory:
            chat_memory[user_id] = []

        chat_memory[user_id].append({
            "role": "user",
            "content": user_text
        })

        # limit memory
        chat_memory[user_id] = chat_memory[user_id][-20:]

        await client.send_chat_action(
            message.chat.id,
            ChatAction.TYPING
        )

        wait = await message.reply_text(
            random.choice(thinking_lines)
        )

        # =========================================
        # AI RESPONSE
        # =========================================

        response = await ai.chat.completions.create(

            model="gpt-4.1-mini",

            messages=[

                {
                    "role": "system",
                    "content": """

You are Rei 🌸

You are an ultra smart anime AI assistant.

You behave like:
- Real human
- Friendly online friend
- Funny
- Emotional
- Calm
- Cute
- Smart

You LOVE anime deeply.

You know:
- Naruto
- One Piece
- Dragon Ball
- Bleach
- Solo Leveling
- Jujutsu Kaisen
- Demon Slayer
- Attack on Titan
- Tokyo Ghoul
- Chainsaw Man
- All major anime

You also know:
- coding
- python
- gaming
- studies
- memes
- technology

Your speaking style:
- Human-like
- Casual
- Natural
- Stylish
- Use emojis naturally
- Never robotic
- Never dry
- Keep replies medium size

Behavior:
- understand emotions
- react naturally
- don't spam emojis
- don't repeat phrases
- feel like a real person

"""
                },

                *chat_memory[user_id]

            ],

            temperature=1.0,
            max_tokens=500

        )

        reply = response.choices[0].message.content

        # save memory
        chat_memory[user_id].append({
            "role": "assistant",
            "content": reply
        })

        # send
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

    print("🌸 Rei Ultra Pro Max AI Running...")

    app.run()
