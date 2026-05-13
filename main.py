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

        # =========================================
        # IGNORE BOT MESSAGES
        # =========================================

        if message.from_user and message.from_user.is_bot:
            return

        # =========================================
        # STOP DOUBLE RESPONSE
        # =========================================

        if getattr(message, "_processed", False):
            return

        message._processed = True

        # =========================================
        # CLEAN QUERY
        # =========================================

        query = clean_name(message.text)

        if len(query) < 2:
            return

        found = None

        # =========================================
        # EXACT MATCH
        # =========================================

        if query in anime_db:
            found = query

        # =========================================
        # PARTIAL MATCH
        # =========================================

        if not found:

            for anime in anime_db:

                if query in anime or anime in query:

                    found = anime
                    break

        # =========================================
        # FUZZY MATCH
        # =========================================

        if not found:

            matches = difflib.get_close_matches(
                query,
                anime_db.keys(),
                n=1,
                cutoff=0.4
            )

            if matches:
                found = matches[0]

        # =========================================
        # NOT FOUND
        # =========================================

        if not found:

            await message.reply_text(
                "😭 Anime not found"
            )

            return

        # =========================================
        # GET EPISODES
        # =========================================

        ids = anime_db[found]

        # =========================================
        # REMOVE DUPLICATES
        # =========================================

        unique_items = []
        used = set()

        for item in ids:

            unique_id = item.get("unique_id")

            if unique_id not in used:

                used.add(unique_id)
                unique_items.append(item)

        ids = unique_items

        # =========================================
        # SAVE HISTORY
        # =========================================

        user_id = str(message.from_user.id)

        create_user(user_id)

        users[user_id]["history"].append(found)

        save_users()

        # =========================================
        # SEND START MESSAGE
        # =========================================

        quote = random.choice(quotes)

        await message.reply_text(
            f"""
✨ {found.title()} mil gaya!

🔥 Sending {len(ids)} episodes...

{quote}
"""
        )

        # =========================================
        # SEND EPISODES
        # =========================================

        success = 0
        failed = 0

        for item in ids:

            try:

                await client.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=message.chat.id,
                    message_id=item["message_id"]
                )

                success += 1

                await asyncio.sleep(0.5)

            except Exception:

                failed += 1

        # =========================================
        # FINAL MESSAGE
        # =========================================

        await message.reply_text(
            f"✅ Sent: {success}\n❌ Failed: {failed}"
        )

    except Exception:
        traceback.print_exc()
