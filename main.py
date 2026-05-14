# =========================================
# 🌸 REI ULTRA AI - COMPLETE OPTIMIZED CODE
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

# =========================================
# ⚙️ CONFIG (Apni Details Yahan Bharien)
# =========================================

# Railway ya VPS pe ho toh Environment Variables use karo, 
# nahi toh direct string dalo
API_ID = int(os.getenv("API_ID", "34695568"))
API_HASH = os.getenv("API_HASH", "fafa070d35e6738bd289023532bad03e")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8143241425:AAGr39PkhCR67jY8aIrsyMgFOxD2VWk9wEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_KEY_HERE")

# 📢 APNI CHANNEL ID (Starting with -100)
CHANNEL_ID = -1002140125432 

# =========================================
# 🤖 AI SETUP (Fixed Model Names)
# =========================================
genai.configure(api_key=GEMINI_API_KEY)

# Fixed: 404 Error se bachne ke liye simplified model names
text_model = genai.GenerativeModel("gemini-1.5-flash")
vision_model = genai.GenerativeModel("gemini-1.5-flash")

DB_FILE = "anime_data.json"
app = Client("rei_v3", API_ID, API_HASH, bot_token=BOT_TOKEN)

# Database Load Logic
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            anime_db = json.load(f)
            if not isinstance(anime_db, dict): anime_db = {}
        except: anime_db = {}
else:
    anime_db = {}

chat_memory = {}

# =========================================
# 🛠️ UTILS
# =========================================
def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(anime_db, f, indent=4)

def clean_name(text):
    text = str(text).lower()
    remove_list = ["1080p", "720p", "480p", "360p", "x264", "aac", "mkv", "mp4", "dual", "audio", "bluray", "webrip"]
    for word in remove_list:
        text = text.replace(word, " ")
    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    return " ".join(text.split())

# =========================================
# 📥 SAVE FROM CHANNEL & FORWARD
# =========================================
@app.on_message((filters.chat(CHANNEL_ID) | filters.forwarded) & (filters.video | filters.document))
async def auto_save_handler(client, message):
    try:
        file_name = (message.video.file_name if message.video else message.document.file_name) or ""
        caption = message.caption or ""
        
        # Anime ka naam nikalna
        anime_name = clean_name(f"{file_name} {caption}")
        if len(anime_name) < 3: return

        if anime_name not in anime_db:
            anime_db[anime_name] = []
        
        # Unique check (Duplicate entry na ho)
        if not any(item['message_id'] == message.id for item in anime_db[anime_name]):
            anime_db[anime_name].append({
                "message_id": message.id, 
                "chat_id": message.chat.id
            })
            save_db()
            
            # Agar bot ko forward kiya hai toh confirmation do
            if message.chat.type == message.chat.type.PRIVATE:
                await message.reply_text(f"✅ **Database Updated:** {anime_name.title()}")
                
    except Exception:
        traceback.print_exc()

# =========================================
# 💬 MAIN SYSTEM (Search + Vision + AI)
# =========================================
@app.on_message(filters.private & ~filters.bot & ~filters.command("start"))
async def main_handler(client, message):
    user_id = str(message.from_user.id)
    
    # 1. PHOTO SEARCH (Identification)
    if message.photo:
        status = await message.reply_text("🔍 Is image ko dekh kar anime dhoond rahi hoon...")
        path = await message.download()
        
        try:
            img = Image.open(path)
            # Vision AI se pucho
            response = vision_model.generate_content([
                "Identify the anime in this thumbnail/image. Just give the anime name, nothing else.", 
                img
            ])
            identified_name = clean_name(response.text)
            os.remove(path)
            
            # Database mein search karo
            found_key = None
            for key in anime_db:
                if identified_name in key or key in identified_name:
                    found_key = key
                    break
            
            if found_key:
                await status.edit_text(f"🌸 Ye **{found_key.title()}** hai! Episodes bhej rahi hoon...")
                for ep in anime_db[found_key]:
                    await client.copy_message(message.chat.id, ep["chat_id"], ep["message_id"])
                    await asyncio.sleep(0.5)
            else:
                await status.edit_text(f"😭 Photo mein **{identified_name.title()}** dikha, par mere database mein abhi nahi hai.")
        except Exception:
            await status.edit_text("❌ Is image ko samajhne mein dikkat hui.")
        return

    # 2. TEXT SEARCH
    user_text = message.text
    if not user_text: return
    
    query = clean_name(user_text)
    found_anime = None
    for key in anime_db:
        if query == key or query in key:
            found_anime = key
            break

    if found_anime:
        await message.reply_text(f"🔥 **{found_anime.title()}** mil gaya! Enjoy...")
        for ep in anime_db[found_anime]:
            await client.copy_message(message.chat.id, ep["chat_id"], ep["message_id"])
            await asyncio.sleep(0.5)
        return

    # 3. AI CHAT (When nothing else matches)
    if user_id not in chat_memory: chat_memory[user_id] = []
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    history = "\n".join([f"{m['r']}: {m['c']}" for m in chat_memory[user_id]])
    prompt = f"""You are Rei, an ultra-smart anime girl AI. 
    You are cool, funny, and talk like a human friend. 
    Current mood: Stylish and helpful.
    
    Context: {history}
    User says: {user_text}
    Rei:"""
    
    try:
        response = text_model.generate_content(prompt)
        reply = response.text
        
        # Save memory
        chat_memory[user_id].append({"r": "User", "c": user_text})
        chat_memory[user_id].append({"r": "Rei", "c": reply})
        chat_memory[user_id] = chat_memory[user_id][-10:]
        
        await message.reply_text(reply)
    except Exception:
        await message.reply_text("🌸 Thoda thak gayi hoon, par tum bolo, main sun rahi hoon! 💕")

# =========================================
# START COMMAND
# =========================================
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text(
        f"🌸 **Hey {message.from_user.first_name}!**\n\n"
        "Main hoon Rei, tumhari Ultra AI Assistant. ✨\n\n"
        "🎬 Anime ka naam likho\n"
        "🖼️ Thumbnail bhejo (Search ke liye)\n"
        "💬 Mujhse baatein karo (Anything!)\n"
        "📥 Files forward karo (Save karne ke liye)"
    )

# =========================================
# EXECUTION
# =========================================
if __name__ == "__main__":
    print("🌸 Rei Ultra AI v3 is Online!")
    app.run()
                
