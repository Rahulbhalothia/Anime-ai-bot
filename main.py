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

STORAGE_CHANNEL = -1002224266205

WELCOME_STICKER = None

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
# STICKER FILE ID GETTER
# =========================================

@app.on_message(filters.sticker)
async def get_sticker_id(client, message):

    try:

        file_id = message.sticker.file_id

        print(file_id)

        await message.reply_text(
            f"✨ Sticker File ID:\n\n{file_id}"
        )

    except Exception:

        traceback.print_exc()

# =========================================
# DATABASE
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
# SAVE DB
# =========================================

def save_db():

    with open(DB_FILE, "w") as f:
        json.dump(anime_db, f, indent=4)

def save_users():

    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=4)

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

        if user_id not in users:

            users[user_id] = {
                "favorites": [],
                "history": []
            }

            save_users()

        if WELCOME_STICKER:

            await message.reply_sticker(
                WELCOME_STICKER
            )

        text = f"""
🌸 Hey {message.from_user.first_name}~

I'm Rei ✨
Your Ultra Anime AI Assistant 😎

🎬 Anime ka naam bhejo.

✨ Example:
• Solo Leveling
• Naruto
• One Piece

🔥 Features:
• Smart Search
• Fast Sending
• Favorites
• Continue Watching
• Anime Recommendations

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
# RUN
# =========================================

print("🌸 Rei Ultra Anime AI Running...")

app.run()
