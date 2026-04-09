from __future__ import annotations

import logging

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from .ai import WriterAI
from .config import SettingsError, get_settings
from .database import Database
from .handlers import WriterBotHandlers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def build_application() -> Application:
    settings = get_settings()
    database = Database(settings.database_path)
    ai_client = WriterAI(settings)
    handlers = WriterBotHandlers(database, ai_client)

    application = ApplicationBuilder().token(settings.telegram_token).build()

    # Commands
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("menu", handlers.start))
    application.add_handler(CommandHandler("stop", handlers.stop_dialog))

    # Callback queries for inline buttons
    application.add_handler(CallbackQueryHandler(handlers.author_selected, pattern=r"^author:\d+$"))
    application.add_handler(CallbackQueryHandler(handlers.show_bio, pattern=r"^bio:\d+$"))
    application.add_handler(CallbackQueryHandler(handlers.show_works, pattern=r"^works:\d+$"))
    application.add_handler(CallbackQueryHandler(handlers.enter_dialog, pattern=r"^dialog:\d+$"))
    application.add_handler(CallbackQueryHandler(handlers.back_to_menu, pattern=r"^menu:\d+$"))
    application.add_handler(CallbackQueryHandler(handlers.end, pattern=r"^end$"))

    # Text messages for dialogue mode
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handlers.handle_dialog_message)
    )

    application.bot_data["database"] = database
    return application


def main() -> None:
    try:
        application = build_application()
    except SettingsError as exc:
        logger.error("Не заданы переменные окружения: %s", exc)
        return

    logger.info("Запуск бота...")
    try:
        application.run_polling()
    finally:
        database = application.bot_data.get("database")
        if database:
            database.close()
            logger.info("База данных закрыта.")
    logger.info("Бот остановлен.")


if __name__ == "__main__":
    main()
