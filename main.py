# =========================================
# 🌸 REI ULTRA PRO ANIME AI ASSISTANT
# =========================================

import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import os
import json
import re
import difflib
import traceback
import random

from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# =========================================
# CONFIG
# =========================================

API_ID = 34695568

API_HASH = "fafa070d35e6738bd289023532bad03e"

BOT_TOKEN = "8143241425:AAGr39PkhCR67jY8aIrsyMgFOxD2VWk9wEY"

DB_FILE = "anime_db.json"

USER_DB = "users.json"

# =========================================
# BOT
# =========================================

app = Client(
    "Rei",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# =========================================
# LOAD DATABASE
# =========================================

if os.path.exists(DB_FILE):

    with open(DB_FILE, "r") as f:
        anime_db = json.load(f)

else:
    anime_db = {}

if os.path.exists(USER_DB):

    with open(USER_DB, "r") as f:
        users = json.load(f)

else:
    users = {}

batch_mode = {}

# =========================================
# SAVE DATABASE
# =========================================

def save_db():

    with open(DB_FILE, "w") as f:
        json.dump(anime_db, f, indent=4)

def save_users():

    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=4)

# =========================================
# CREATE USER
# =========================================

def create_user(user_id):

    user_id = str(user_id)

    if user_id not in users:

        users[user_id] = {

            "favorites": [],
            "history": []

        }

        save_users()

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
        "hindi",
        "english",
        "dual",
        "audio",
        "bluray",
        "webrip",
        "sub",
        "dub",
        "official",
        "episode",
        "ep",
        "season"

    ]

    for word in remove_words:

        name = name.replace(word, "")

    name = re.sub(r"\d+", "", name)

    name = re.sub(r"[^a-zA-Z ]", "", name)

    return name.replace(" ", "").strip()

# =========================================
# QUOTES
# =========================================

quotes = [

    "⚡ Wake up to reality.",
    "🌸 Power comes from within.",
    "🔥 Keep moving forward.",
    "✨ Anime makes life better.",
    "😎 Shadows are strongest."

]

# =========================================
# START
# =========================================

@app.on_message(filters.command("start"))
async def start(client, message):

    try:

        user_id = str(message.from_user.id)

        create_user(user_id)

        text = f"""
🌸 Hey {message.from_user.first_name}~

I'm Rei ✨
Your Ultra Anime AI Assistant 😎

🎬 Anime ka naam bhejo

✨ Example:
• Solo Leveling
• Naruto
• One Piece

🔥 Features:
• Smart Search
• Fast Sending
• Favorites
• No Duplicate Episodes

⚡ Batch Save:
/batch sololeveling
"""

        buttons = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🔥 Action",
                    callback_data="action"
                ),

                InlineKeyboardButton(
                    "💕 Romance",
                    callback_data="romance"
                )
            ],

            [
                InlineKeyboardButton(
                    "⚔ Isekai",
                    callback_data="isekai"
                ),

                InlineKeyboardButton(
                    "😂 Comedy",
                    callback_data="comedy"
                )
            ]
        ])

        await message.reply_photo(
            photo="welcome.png",
            caption=text,
            reply_markup=buttons
        )

    except Exception:

        traceback.print_exc()

# =========================================
# BUTTONS
# =========================================

@app.on_callback_query()
async def buttons(client, callback):

    try:

        data = callback.data

        anime_lists = {

            "action": [
                "Solo Leveling",
                "Jujutsu Kaisen",
                "Demon Slayer"
            ],

            "romance": [
                "Horimiya",
                "Toradora",
                "Your Lie In April"
            ],

            "isekai": [
                "Overlord",
                "ReZero",
                "Mushoku Tensei"
            ],

            "comedy": [
                "Grand Blue",
                "Gintama",
                "Konosuba"
            ]
        }

        if data in anime_lists:

            text = "✨ Recommended Anime:\n\n"

            for anime in anime_lists[data]:

                text += f"• {anime}\n"

            await callback.message.reply_text(text)

    except Exception:

        traceback.print_exc()

# =========================================
# BATCH MODE
# =========================================

@app.on_message(filters.command("batch"))
async def batch(client, message):

    try:

        args = message.text.split(maxsplit=1)

        if len(args) < 2:

            await message.reply_text(
                "❌ Usage:\n/batch sololeveling"
            )

            return

        anime_name = clean_name(args[1])

        batch_mode[message.chat.id] = anime_name

        await message.reply_text(
            f"🔥 Batch mode ON for {anime_name}"
        )

    except Exception:

        traceback.print_exc()

# =========================================
# STOP BATCH
# =========================================

@app.on_message(filters.command("stopbatch"))
async def stop_batch(client, message):

    try:

        if message.chat.id in batch_mode:

            del batch_mode[message.chat.id]

        await message.reply_text(
            "🛑 Batch mode OFF"
        )

    except Exception:

        traceback.print_exc()

# =========================================
# AUTO SAVE
# =========================================

@app.on_message(filters.video | filters.document)
async def auto_save(client, message):

    try:

        if message.chat.id not in batch_mode:
            return

        anime_name = batch_mode[message.chat.id]

        if anime_name not in anime_db:

            anime_db[anime_name] = []

        # UNIQUE FILE ID
        if message.video:
            unique_id = message.video.file_unique_id
        else:
            unique_id = message.document.file_unique_id

        # CHECK DUPLICATE
        already_saved = False

        for item in anime_db[anime_name]:

            if item["file_id"] == unique_id:

                already_saved = True
                break

        if already_saved:

            await message.reply_text(
                "⚠ Already Saved"
            )

            return

        # SAVE
        anime_db[anime_name].append({

            "file_id": unique_id,
            "message_id": message.id

        })

        save_db()

        total = len(anime_db[anime_name])

        await message.reply_text(
            f"✅ Saved in {anime_name}\n📦 Total Episodes: {total}"
        )

    except Exception:

        traceback.print_exc()

# =========================================
# MANUAL SAVE
# =========================================

@app.on_message(filters.reply & filters.text)
async def manual_save(client, message):

    try:

        replied = message.reply_to_message

        if not replied:
            return

        if not (replied.video or replied.document):
            return

        anime_name = clean_name(message.text)

        if len(anime_name) < 2:
            return

        if anime_name not in anime_db:

            anime_db[anime_name] = []

        # UNIQUE FILE ID
        if replied.video:
            unique_id = replied.video.file_unique_id
        else:
            unique_id = replied.document.file_unique_id

        # CHECK DUPLICATE
        already_saved = False

        for item in anime_db[anime_name]:

            if item["file_id"] == unique_id:

                already_saved = True
                break

        if already_saved:

            await message.reply_text(
                "⚠ Already Saved"
            )

            return

        # SAVE
        anime_db[anime_name].append({

            "file_id": unique_id,
            "message_id": replied.id

        })

        save_db()

        total = len(anime_db[anime_name])

        await message.reply_text(
            f"✨ Saved in {anime_name}\n📦 Total Episodes: {total}"
        )

    except Exception:

        traceback.print_exc()

# =========================================
# FAVORITES
# =========================================

@app.on_message(filters.command("fav"))
async def favorite(client, message):

    try:

        args = message.text.split(maxsplit=1)

        if len(args) < 2:
            return

        anime = clean_name(args[1])

        user_id = str(message.from_user.id)

        create_user(user_id)

        if anime not in users[user_id]["favorites"]:

            users[user_id]["favorites"].append(anime)

            save_users()

        await message.reply_text(
            f"💕 Added {anime} to favorites"
        )

    except Exception:

        traceback.print_exc()

# =========================================
# SEARCH
# =========================================

@app.on_message(filters.text & ~filters.command([
    "start",
    "batch",
    "stopbatch",
    "fav"
]))
async def search(client, message):

    try:

        query = clean_name(message.text)

        if len(query) < 2:
            return

        found = None

        for anime in anime_db:

            if query in anime or anime in query:

                found = anime
                break

        if not found:

            matches = difflib.get_close_matches(
                query,
                anime_db.keys(),
                n=1,
                cutoff=0.5
            )

            if matches:

                found = matches[0]

        if not found:

            await message.reply_text(
                "😭 Anime not found"
            )

            return

        ids = anime_db[found]

        user_id = str(message.from_user.id)

        create_user(user_id)

        users[user_id]["history"].append(found)

        save_users()

        quote = random.choice(quotes)

        await message.reply_text(
            f"""
✨ {found.title()} mil gaya!

🔥 Sending {len(ids)} episodes...

{quote}
"""
        )

        success = 0
        failed = 0

        for item in ids:

            try:

                msg_id = item["message_id"]

                await client.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=message.chat.id,
                    message_id=msg_id
                )

                success += 1

                await asyncio.sleep(0.3)

            except Exception:

                failed += 1

                traceback.print_exc()

        await message.reply_text(
            f"✅ Sent: {success}\n❌ Failed: {failed}"
        )

    except Exception:

        traceback.print_exc()

# =========================================
# RUN
# =========================================

print("🌸 Rei Ultra Anime AI Running...")

app.run()
