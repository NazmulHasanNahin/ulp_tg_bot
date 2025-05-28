import os
import logging
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from parser import process_zip_file
from google_drive import upload_file_to_drive, create_shareable_link

# =========== Bot Config ===========
BOT_TOKEN = "7804596940:AAGEiCQI8UKyeLrQMJ-UpTHrsSDHJ2N8l90"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = 45 * 1024 * 1024  # 45MB

# =========== Logging ===========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========== Storage ===========
user_keywords = {}

# =========== Command Handlers ===========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 হ্যালো!\n"
        "এই বটে ফাইল থেকে আপনার পছন্দের যেকোনো শব্দ বা ডোমেইন খুঁজে বের করতে পারবেন।\n"
        "প্রথমে /get [শব্দ/ডোমেইন] কমান্ড দিয়ে কিওয়ার্ড সেট করুন।\n"
        "তারপর .zip, .rar অথবা .txt ফাইল পাঠান।\n"
        "ফিচার দেখতে /cmd লিখুন।\n\n"
        "_Created by Nazmul Hasan Nahin_"
    )

async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔘 *বট এর ফিচার ও কমান্ডসমূহ:*\n\n"
        "1️⃣ `/get yourkeyword` - যেকোনো শব্দ/ডোমেইন সেট করুন (যেমন: `/get example.com`).\n"
        "2️⃣ আর্কাইভ (.zip/.rar) অথবা টেক্সট (.txt) ফাইল পাঠান, বট সেট করা কিওয়ার্ড অনুসন্ধান করবে।\n"
        "3️⃣ বড় ফাইল হলে অটো Google Drive-এ আপলোড হবে ও শেয়ার লিংক দিবে।\n"
        "4️⃣ `/cmd` - এই নির্দেশিকা দেখুন।\n\n"
        "👉 প্রথমে অবশ্যই `/get` দিয়ে কিওয়ার্ড সেট করুন, না হলে বট কাজ করবে না!\n\n"
        "_Created by Nazmul Hasan Nahin_",
        parse_mode="Markdown"
    )

async def set_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        keyword = " ".join(context.args).strip()
        user_keywords[update.effective_user.id] = keyword
        await update.message.reply_text(
            f"✅ এখন থেকে `{keyword}` খোঁজা হবে!\nএখন .zip, .rar অথবা .txt ফাইল পাঠান।",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("⚠️ দয়া করে কিওয়ার্ড/ডোমেইন দিন! যেমন: `/get example.com`", parse_mode="Markdown")

# =========== File Handler ===========

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyword = user_keywords.get(user_id)

    if not keyword:
        await update.message.reply_text("❌ আগে `/get` দিয়ে কিওয়ার্ড সেট করুন!", parse_mode="Markdown")
        return

    try:
        file = update.message.document
        file_name = file.file_name
        file_size = file.file_size
        file_path = os.path.join(DOWNLOAD_DIR, file_name)

        logger.info(f"📁 Received file: {file_name}, Size: {file_size}")

        # Large file upload to drive
        if file_size > MAX_FILE_SIZE:
            await update.message.reply_text("⚠️ ফাইলটি বড়, Google Drive-এ আপলোড করা হবে...")
            file_obj = await file.get_file()
            await file_obj.download_to_drive(custom_path=file_path)
            logger.info(f"📥 File downloaded: {file_path}")
            drive_file_id = upload_file_to_drive(file_path)
            link = create_shareable_link(drive_file_id)
            await update.message.reply_text(f"📎 Google Drive লিংক:\n{link}")
            return

        # Normal processing
        await update.message.reply_text("📥 ফাইল ডাউনলোড হচ্ছে...")
        file_obj = await file.get_file()
        await file_obj.download_to_drive(custom_path=file_path)
        await update.message.reply_text(f"📂 ফাইল `{file_name}` প্রসেস করা হচ্ছে...", parse_mode="Markdown")

        result_file, count = None, 0
        if file_name.endswith((".zip", ".rar")):
            result_file, count = process_zip_file(file_path, keyword)
        elif file_name.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            matches = [line for line in lines if keyword in line]
            result_file = os.path.join(DOWNLOAD_DIR, "result.txt")
            with open(result_file, "w", encoding="utf-8") as f:
                f.writelines(matches)
            count = len(matches)
        else:
            await update.message.reply_text("❌ এই ফাইল টাইপ সাপোর্টেড না।")
            return

        await update.message.reply_text(f"✅ `{keyword}` পাওয়া গেছে {count} বার।", parse_mode="Markdown")

        if result_file and os.path.getsize(result_file) > MAX_FILE_SIZE:
            drive_file_id = upload_file_to_drive(result_file)
            link = create_shareable_link(drive_file_id)
            await update.message.reply_text(f"📎 রেজাল্ট ফাইল বড়, Google Drive লিংক:\n{link}")
        else:
            with open(result_file, "rb") as f:
                await update.message.reply_document(f, filename=os.path.basename(result_file))

    except Exception as e:
        logger.error("❌ File processing error", exc_info=True)
        await update.message.reply_text(f"❌ সমস্যা হয়েছে:\n{str(e)}")

    finally:
        for file_path_to_clean in [file_path, result_file]:
            if file_path_to_clean and os.path.exists(file_path_to_clean):
                try:
                    os.remove(file_path_to_clean)
                except Exception as e:
                    logger.warning(f"⚠️ Cleanup failed: {e}")

# =========== Main ===========

async def main():
    print("🤖 Bot is starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cmd", cmd))
    app.add_handler(CommandHandler("get", set_keyword))
    app.add_handler(MessageHandler(
        filters.Document.FileExtension("zip")
        | filters.Document.FileExtension("rar")
        | filters.Document.FileExtension("txt"),
        handle_file
    ))

    await app.run_polling()

# =========== Entry Point (Render-compatible) ===========

import asyncio
import nest_asyncio

import sys

from bot import main  # যদি সব কোড এক ফাইলে থাকে তাহলে শুধু main() রাখলেই হবে

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise
