from pyrogram import Client
import os
from dotenv import load_dotenv
load_dotenv()

API_ID   = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client(
    "temp_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

with app:
    session = app.export_session_string()
    print("\n" + "="*60)
    print("YOUR SESSION STRING:")
    print("="*60)
    print(session)
    print("="*60 + "\n")
    print("Isko copy karo aur Railway mein SESSION_STRING variable mein daalo!")
  
