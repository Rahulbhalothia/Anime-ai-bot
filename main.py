# =========================================
# BOT
# =========================================

app = Client(
    "Rei",
    API_ID = 34695568
API_HASH = "fafa070d35e6738bd289023532bad03e"
BOT_TOKEN = "8143241425:AAGr39PkhCR67jY8aIrsyMgFOxD2VWk9wEY"

app = Client(
    "Rei",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)
)

# =========================================
# SEARCH
# =========================================

@app.on_message(
    filters.text &
    ~filters.reply &
    ~filters.forwarded &
    ~filters.command([
        "start",
        "batch",
        "stopbatch",
        "fav"
    ])
)
async def search(client, message):

    try:

        # IGNORE BOT MESSAGES
        if message.from_user and message.from_user.is_bot:
            return

        # CLEAN QUERY
        query = clean_name(message.text)

        if len(query) < 2:
            return

        found = None

        # EXACT MATCH
        if query in anime_db:
            found = query

        # PARTIAL MATCH
        if not found:

            for anime in anime_db:

                if query in anime or anime in query:
                    found = anime
                    break

        # FUZZY MATCH
        if not found:

            matches = difflib.get_close_matches(
                query,
                anime_db.keys(),
                n=1,
                cutoff=0.4
            )

            if matches:
                found = matches[0]

        # NOT FOUND
        if not found:

            await message.reply_text(
                "😭 Anime not found"
            )

            return

        # GET SAVED EPISODES
        ids = anime_db[found]

        # REMOVE DUPLICATES
        unique_items = []
        used = set()

        for item in ids:

            unique_id = item.get("unique_id")

            if unique_id not in used:

                used.add(unique_id)
                unique_items.append(item)

        ids = unique_items

        # SAVE HISTORY
        user_id = str(message.from_user.id)

        create_user(user_id)

        users[user_id]["history"].append(found)

        save_users()

        # RANDOM QUOTE
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

        # SEND EPISODES
        for item in ids:

            try:

                await client.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=message.chat.id,
                    message_id=item["message_id"]
                )

                success += 1

                await asyncio.sleep(0.5)

            except Exception as e:

                print(e)

                failed += 1

        # FINAL STATUS
        await message.reply_text(
            f"✅ Sent: {success}\n❌ Failed: {failed}"
        )

    except Exception:
        traceback.print_exc()
