# =========================================
# EXTRA FEATURES UPDATE FOR REI
# ADD THIS BELOW SEARCH SYSTEM
# =========================================

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
# HELP COMMAND
# =========================================

@app.on_message(filters.command("help"))
async def help_command(client, message):

    try:

        text = """
🌸 Rei Help Menu

🎬 Anime Search:
Just send anime name

Example:
Solo Leveling

📥 Save Anime:
Reply anime name on forwarded anime

Example:
sololeveling

⚡ Batch Save:
/batch sololeveling

🛑 Stop Batch:
/stopbatch

💕 Favorites:
/fav sololeveling
"""

        await message.reply_text(text)

    except Exception:

        traceback.print_exc()

# =========================================
# HISTORY COMMAND
# =========================================

@app.on_message(filters.command("history"))
async def history(client, message):

    try:

        user_id = str(message.from_user.id)

        if user_id not in users:
            return

        history_list = users[user_id]["history"]

        if len(history_list) == 0:

            await message.reply_text(
                "😭 No watch history found"
            )

            return

        text = "🕒 Recent Watched Anime:\n\n"

        for anime in history_list[-10:]:

            text += f"• {anime.title()}\n"

        await message.reply_text(text)

    except Exception:

        traceback.print_exc()

# =========================================
# FAVORITES LIST
# =========================================

@app.on_message(filters.command("favorites"))
async def favorites(client, message):

    try:

        user_id = str(message.from_user.id)

        if user_id not in users:
            return

        favs = users[user_id]["favorites"]

        if len(favs) == 0:

            await message.reply_text(
                "😭 No favorites added"
            )

            return

        text = "💕 Your Favorite Anime:\n\n"

        for anime in favs:

            text += f"• {anime.title()}\n"

        await message.reply_text(text)

    except Exception:

        traceback.print_exc()

# =========================================
# RANDOM ANIME QUOTE
# =========================================

@app.on_message(filters.command("quote"))
async def anime_quote(client, message):

    try:

        quote = random.choice(quotes)

        await message.reply_text(
            f"🌸 Anime Quote:\n\n{quote}"
        )

    except Exception:

        traceback.print_exc()

# =========================================
# CONTINUE WATCHING
# =========================================

@app.on_message(filters.command("continue"))
async def continue_watch(client, message):

    try:

        user_id = str(message.from_user.id)

        if user_id not in users:
            return

        history_list = users[user_id]["history"]

        if len(history_list) == 0:

            await message.reply_text(
                "😭 No recent anime found"
            )

            return

        anime = history_list[-1]

        await message.reply_text(
            f"▶ Continue Watching:\n\n{anime.title()}"
        )

    except Exception:

        traceback.print_exc()
