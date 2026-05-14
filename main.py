# =========================================
# 🌸 REI ULTRA AI - VISION + CHAT + SAVE
# =========================================

import os
import re
import json
import asyncio
import random
import traceback
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
import google.generativeai as genai
from PIL import Image
import io

# =========================================
# CONFIG
# =========================================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# AI MODELS
genai.configure(api_key=GEMINI_API_KEY)
text_model = genai.GenerativeModel("gemini-1.5-flash")
vision_model = genai.GenerativeModel("gemini-1.5-flash") # Vision support included

DB_FILE = "anime_data.json"
app = Client("rei_v3", API_ID, API_HASH, bot_token=BOT_TOKEN)

# Load DB
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f: anime_db = json.load(f)
else: anime_db = {}

chat_memory = {}

# =========================================
# UTILS
# =========================================
def save_db():
    with open(DB_FILE, "w") as f: json.dump(anime_db, f, indent=4)

def clean_name(text):
    return " ".join(re.sub(r'[^a-zA-Z0-9 ]', '', text.lower()).split())

# =========================================
# IMAGE SE ANIME PEHCHANNA (VISION)
# =========================================
async def identify_anime_from_image(photo_path):
    try:
        img = Image.open(photo_path)
        prompt = "Identify the anime in this image. Only give the anime name, nothing else."
        response = vision_model.generate_content([prompt, img])
        return clean_name(response.text)
    except:
        return None

# =========================================
# 📥 SAVE & FORWARD LOGIC
# =========================================
@app.on_message(filters.forwarded & (filters.video | filters.document))
async def save_forwarded_anime(client, message):
    # Jab aap kisi channel se bot ko forward karoge
    file_name = (message.video.file_name if message.video else message.document.file_name) or "Unknown"
    caption = message.caption or ""
    
    # AI se pucho context kya hai
    anime_name = clean_name(f"{file_name} {caption}")
    
    if anime_name not in anime_db: anime_db[anime_name] = []
    
    entry = {"message_id": message.id, "chat_id": message.chat.id}
    if entry not in anime_db[anime_name]:
        anime_db[anime_name].append(entry)
        save_db()
        await message.reply_text(f"✅ **Saved in Database:** {anime_name.title()}")

# =========================================
# 💬 MAIN CHAT + SEARCH + VISION
# =========================================
@app.on_message(filters.private & ~filters.bot)
async def rei_main_handler(client, message):
    user_id = str(message.from_user.id)
    
    # 1. AGAR USER PHOTO BHEJE (Thumbnail Search)
    if message.photo:
        wait = await message.reply_text("🔍 Thumbnail se anime dhoond rahi hoon...")
        path = await message.download()
        anime_name = await identify_anime_from_image(path)
        os.remove(path)
        
        if anime_name and anime_name in anime_db:
            await wait.edit_text(f"🌸 Photo dekh kar lag raha hai ye **{anime_name.title()}** hai! Episodes bhej rahi hoon...")
            for ep in anime_db[anime_name]:
                await client.copy_message(message.chat.id, ep["chat_id"], ep["message_id"])
                await asyncio.sleep(0.5)
        else:
            await wait.edit_text(f"😭 Sorry! Photo mein shayad {anime_name} hai, par mere database mein nahi mila.")
        return

    # 2. AGAR USER TEXT BHEJE
    user_text = message.text
    query = clean_name(user_text)

    # Search in DB
    found_anime = None
    for key in anime_db:
        if query in key or key in query:
            found_anime = key
            break

    if found_anime:
        await message.reply_text(f"🔥 {found_anime.title()} ke episodes mil gaye! Enjoy!")
        for ep in anime_db[found_anime]:
            await client.copy_message(message.chat.id, ep["chat_id"], ep["message_id"])
            await asyncio.sleep(0.5)
        return

    # 3. FULL AI CHAT (Agar anime nahi mila toh baatein karo)
    if user_id not in chat_memory: chat_memory[user_id] = []
    
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    history = "\n".join([f"{m['r']}: {m['c']}" for m in chat_memory[user_id]])
    system_prompt = f"You are Rei, a stylish, funny, and emotional anime girl AI. You love talking about everything from coding to life. Keep it natural.\n{history}\nUser: {user_text}\nRei:"
    
    try:
        response = text_model.generate_content(system_prompt)
        reply = response.text
        
        # Memory update
        chat_memory[user_id].append({"r": "User", "c": user_text})
        chat_memory[user_id].append({"r": "Rei", "c": reply})
        chat_memory[user_id] = chat_memory[user_id][-10:]
        
        await message.reply_text(reply)
    except:
        await message.reply_text("🌸 Rei is a bit busy, can we talk in a bit? 💕")

# =========================================
# START
# =========================================
print("🌸 Rei Vision & Chat Bot Online!")
app.run()
        
