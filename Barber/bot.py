import io
import logging
from telegram import Update, InputMediaPhoto, ReplyKeyboardMarkup, WebAppInfo, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ChatAction

from config import (
    TELEGRAM_BOT_TOKEN,
    WELCOME_MESSAGE,
    PROCESSING_MESSAGE,
    ERROR_MESSAGE,
    NO_FACE_MESSAGE,
    SNAKE_WEBAPP_URL,
)
from openai_service import analyze_photo_and_get_hairstyles, generate_all_hairstyle_images

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Choose Hair Style")],
        [KeyboardButton("Play", web_app=WebAppInfo(url=SNAKE_WEBAPP_URL))],
    ],
    resize_keyboard=True,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /start command."""
    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=MAIN_MENU_KEYBOARD)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /help command."""
    await update.message.reply_text(
        "How to use this bot:\n\n"
        "1. Take or choose a clear photo of your face\n"
        "2. Send it to this chat\n"
        "3. Wait while AI analyzes your features (~30-60 seconds)\n"
        "4. Receive 6 personalized hairstyle options!\n\n"
        "Or tap 'Play' to play the Snake game!\n\n"
        "For best results use a well-lit, front-facing photo.",
        reply_markup=MAIN_MENU_KEYBOARD,
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main handler: receives user photo, runs AI analysis,
    generates 6 hairstyle options, sends them back.
    """
    user = update.effective_user
    logger.info(f"Received photo from user {user.id} (@{user.username})")

    # Send processing message
    processing_msg = await update.message.reply_text(PROCESSING_MESSAGE)

    try:
        # Download the highest-resolution version of the photo
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.UPLOAD_PHOTO,
        )

        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        logger.info(f"Downloaded photo ({len(photo_bytes)} bytes) from user {user.id}")

        # Step 1: Analyze photo with GPT-4 Vision
        await processing_msg.edit_text(
            "Step 1/3: Analyzing your face shape and hair type..."
        )

        analysis = await analyze_photo_and_get_hairstyles(bytes(photo_bytes))

        hairstyles = analysis.get("hairstyles", [])
        if not hairstyles:
            await processing_msg.edit_text(NO_FACE_MESSAGE)
            return

        hair_type = analysis.get("hair_type", "unknown")
        logger.info(
            f"Analysis for user {user.id}: hair={hair_type}, "
            f"styles={len(hairstyles)}"
        )

        # Step 2: Edit original photo with gpt-image-1
        await processing_msg.edit_text(
            f"Step 2/3: Generating 6 hairstyle options on your photo...\n"
            "This takes about 30-60 seconds."
        )

        generated = await generate_all_hairstyle_images(analysis, bytes(photo_bytes))

        if not generated:
            await processing_msg.edit_text(ERROR_MESSAGE)
            return

        # Step 3: Send results
        await processing_msg.edit_text(
            f"Step 3/3: Sending your {len(generated)} hairstyle options..."
        )

        # Build summary caption
        summary_lines = [
            f"Here are your {len(generated)} personalized hairstyle options!\n",
            f"Hair type: {hair_type}\n",
        ]
        for i, style in enumerate(generated, 1):
            summary_lines.append(f"{i}. {style['name']}")

        await update.message.reply_text("\n".join(summary_lines))

        # Send each hairstyle as a photo with caption
        for i, style in enumerate(generated, 1):
            caption = (
                f"Option {i}: {style['name']}\n\n"
                f"{style['reason']}"
            )
            # Truncate caption to Telegram's 1024-char limit
            if len(caption) > 1024:
                caption = caption[:1021] + "..."

            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(style["image_bytes"]),
                caption=caption,
            )

        await processing_msg.delete()
        await update.message.reply_text(
            "Done! Show these to your barber and pick your favorite style."
        )

        logger.info(f"Successfully sent {len(generated)} hairstyles to user {user.id}")

    except Exception as e:
        logger.error(f"Error processing photo for user {user.id}: {e}", exc_info=True)
        await processing_msg.edit_text(ERROR_MESSAGE)


async def handle_choose_hair_style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the 'Choose Hair Style' button."""
    await update.message.reply_text(
        "Please send me a photo of your face to get hairstyle recommendations.",
        reply_markup=MAIN_MENU_KEYBOARD,
    )


async def handle_non_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text or non-photo messages."""
    await update.message.reply_text(
        "Please send me a photo of your face to get hairstyle recommendations.\n"
        "Or tap 'Play' to play the Snake game!\n"
        "Use /start to see instructions.",
        reply_markup=MAIN_MENU_KEYBOARD,
    )


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env file")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Regex(r"^Choose Hair Style$"), handle_choose_hair_style))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_photo)
    )

    logger.info("Barber Style Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
