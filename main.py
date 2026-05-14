import os
import re
import json
import asyncio
import traceback
import io
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
import google.generativeai as genai
from PIL import Image

# =========================================
# ⚙️ CONFIG (Apni Details Yahan Bharien)
# =========================================
# Railway Dashboard mein ye Variables set karein
API_ID = int(os.getenv("API_ID", "34695568"))
API_HASH = os.getenv("API_HASH", "fafa070d35e6738bd289023532bad03e")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8143241425:AAGr39PkhCR67jY8aIrsyMgFOxD2VWk9wEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_KEY_HERE")

# 👑 ADMIN & CHANNEL (Must Change This)
ADMIN_ID = 123456789  # <--- Apni numeric ID dalo
CHANNEL_ID = -1002140125432 # <--- Apne channel ki ID

# =========================================
# 🤖 AI SETUP (Gemini 1.5 Flash)
# =========================================
genai.configure(api_key=GEMINI_API_KEY)
# Fixed Model Name for Railway Stability
model = genai.GenerativeModel("gemini-1.5-flash")

DB_FILE = "anime_data.json"
app = Client("rei_final_vision", API_ID, API_HASH, bot_token=BOT_TOKEN)

# Load Database
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            anime_db = json.load(f)
            if not isinstance(anime_db, dict): anime_db = {}
        except: anime_db = {}
else:
    anime_db = {}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(anime_db, f, indent=4)

def clean_name(text):
    text = str(text).lower()
    # Remove quality tags for cleaner database keys
    remove_list = ["1080p", "720p", "480p", "360p", "x264", "aac", "mkv", "mp4", "dual", "audio", "bluray", "webrip"]
    for word in remove_list:
        text = text.replace(word, " ")
    return " ".join(re.sub(r'[^a-zA-Z0-9 ]', '', text).split())

# =========================================
# 🖼️ VISION: IDENTIFY ANIME FROM THUMBNAIL
# =========================================
async def get_anime_name_via_ai(client, message):
    try:
        # Step 1: Video ka thumbnail memory mein download karna (Storage bachega)
        photo = await client.download_media(message, in_memory=True)
        img = Image.open(io.BytesIO(photo.getbuffer()))
        
        # Step 2: Gemini Vision se naam puchna
        prompt = "Analyze this anime thumbnail/frame. Identify the anime name. Reply with ONLY the official name of the anime, no extra text."
        response = model.generate_content([prompt, img])
        
        return clean_name(response.text)
    except Exception as e:
        print(f"Vision Error: {e}")
        return None

# =========================================
# 📥 MASTER INDEXING (Admin Forward & Auto-Channel)
# =========================================
@app.on_message((filters.chat(CHANNEL_ID) | (filters.user(ADMIN_ID) & filters.forwarded)) & (filters.video | filters.document))
async def master_save_handler(client, message):
    try:
        # AI pehle thumbnail se pehchanega
        anime_name = await get_anime_name_via_ai(client, message)
        
        # Backup: Agar AI fail ho toh file name use karega
        if not anime_name or len(anime_name) < 2:
            file_obj = message.video or message.document
            anime_name = clean_name(file_obj.file_name or "unknown_anime")

        if anime_name not in anime_db:
            anime_db[anime_name] = []
        
        # Duplicate entry check (Message ID save karega copy karne ke liye)
        if not any(item['message_id'] == message.id for item in anime_db[anime_name]):
            anime_db[anime_name].append({
                "message_id": message.id, 
                "chat_id": message.chat.id
            })
            save_db()
            print(f"✅ AI Indexed: {anime_name.title()}")
            
            # Aapko (Admin) confirm karega agar aap forward karte ho
            if message.chat.type == message.chat.type.PRIVATE:
                await message.reply_text(f"🚀 **AI Identified & Saved!**\nName: `{anime_name.title()}`\nStatus: Added to Batch Database.")
    except Exception:
        traceback.print_exc()

# =========================================
# 💬 USER CHAT & SMART SEARCH
# =========================================
@app.on_message(filters.private & ~filters.bot & ~filters.command("start"))
async def main_chat_handler(client, message):
    user_text = message.text
    if not user_text: return
    
    query = clean_name(user_text)
    
    # 1. SEARCH: Database mein AI ka pehchana hua naam dhoondna
    found_key = None
    for key in anime_db:
        if query in key or key in query:
            found_key = key
            break

    if found_key:
        await message.reply_text(f"🔥 **{found_key.title()}** mil gaya! Episodes bhej rahi hoon...")
        for ep in anime_db[found_key]:
            try:
                await client.copy_message(message.chat.id, ep["chat_id"], ep["message_id"])
                await asyncio.sleep(0.5) # Copy speed control
            except:
                continue
        return

    # 2. AI CHAT: Agar anime nahi mila, toh dosti waali baatein
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    try:
        prompt = f"You are Rei, a stylish and cool anime expert AI. Answer in friendly Hinglish. Keep it short and human-like. User says: {user_text}"
        response = model.generate_content(prompt)
        await message.reply_text(response.text)
    except:
        await message.reply_text("🌸 Rei thoda thak gayi hai, par main sun rahi hoon! 💕")

# =========================================
# START COMMAND
# =========================================
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text(
        f"🌸 **Hey {message.from_user.first_name}!**\n\n"
        "Main Rei hoon, tumhari Smart Anime AI. 😎\n\n"
        "🎬 Bas anime ka naam likho, main bhej dungi!\n"
        "💬 Mujhse kuch bhi baatein karo, main bore nahi hone dungi.\n"
        "✨ AI Power: Maine images dekh kar sab pehchaan rakha hai!"
    )

# =========================================
# RUN BOT
# =========================================
if __name__ == "__main__":
    print("🌸 Rei Ultra Vision AI v3 is Online!")
    app.run()
