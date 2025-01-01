import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

# MongoDB setup
mongo_url = "mongodb+srv://Werewolf_Demon:Werewolf_Demon@werewolfdemon.ebsu8.mongodb.net/?retryWrites=true&w=majority&appName=werewolfdemon"
client = AsyncIOMotorClient(mongo_url)
db = client["ariop"]  # Replace with your database name
usersdb = db["users"]  # Replace with your users collection name
chatsdb = db["chats"]  # Replace with your chats collection name

# Global Flag for Broadcasting
IS_BROADCASTING = False

async def get_served_users() -> list:
    """Fetch all served users from the database."""
    users_list = []
    async for user in usersdb.find({"user_id": {"$gt": 0}}):
        users_list.append(user)
    return users_list

async def get_served_chats() -> list:
    """Fetch all served chats from the database."""
    chats_list = []
    async for chat in chatsdb.find({"chat_id": {"$lt": 0}}):
        chats_list.append(chat)
    return chats_list

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast messages to all served chats."""
    global IS_BROADCASTING

    # Only allow sudoers (bot admins)
    sudoers = [6545754981, 7379318591]  # Replace with actual user IDs of bot admins
    if update.effective_user.id not in sudoers:
        await update.message.reply_text("You don't have permission to use this command.")
        return

    if IS_BROADCASTING:
        await update.message.reply_text("A broadcast is already in progress. Please wait.")
        return

    if not update.message.reply_to_message and len(context.args) == 0:
        await update.message.reply_text("Please reply to a message or provide text to broadcast.")
        return

    IS_BROADCASTING = True
    sent_count = 0
    pin_count = 0

    # Determine message content
    if update.message.reply_to_message:
        forward_message_id = update.message.reply_to_message.message_id
        forward_chat_id = update.message.chat_id
        broadcast_text = None
    else:
        broadcast_text = " ".join(context.args)

    await update.message.reply_text("Broadcasting started. Please wait...")

    # Get all served chats
    chats = await get_served_chats()
    for chat in chats:
        chat_id = chat["chat_id"]
        try:
            # Forward or send the message
            if broadcast_text:
                await context.bot.send_message(chat_id=chat_id, text=broadcast_text)
            else:
                await context.bot.forward_message(
                    chat_id=chat_id,
                    from_chat_id=forward_chat_id,
                    message_id=forward_message_id,
                )
            sent_count += 1

            # Optional: Pin message
            if broadcast_text and "-pin" in broadcast_text:
                try:
                    await context.bot.pin_chat_message(
                        chat_id=chat_id, message_id=update.message.message_id
                    )
                    pin_count += 1
                except:
                    continue

            await asyncio.sleep(0.2)  # Rate limiting
        except TelegramError:
            continue  # Skip failed chats

    # Completion message
    await update.message.reply_text(f"Broadcast completed: Sent to {sent_count} chats, pinned in {pin_count} chats.")
    IS_BROADCASTING = False