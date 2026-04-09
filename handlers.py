from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from .ai import WriterAI
from .database import Database
from .keyboards import author_menu_keyboard, author_selection_keyboard, back_to_menu_keyboard


class WriterBotHandlers:
    def __init__(self, database: Database, ai: WriterAI) -> None:
        self._db = database
        self._ai = ai

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        authors = self._db.list_authors()
        if not authors:
            if update.message:
                await update.message.reply_text("База писателей пуста. Добавьте данные и попробуйте снова.")
            return

        welcome_text = (
            "Добро пожаловать в бот для общения с великим писателем!\n\n"
            "✨ Возможности бота:\n"
            "• 💬 Общение с писателем в режиме диалога\n"
            "• 📖 Просмотр биографий и произведений\n"
            "• 📝 Чтение стихов и отрывков из произведений\n"
            "• ✍️ Генерация текстов в стиле писателя\n\n"
            "Выберите автора, чтобы начать:"
        )

        keyboard = author_selection_keyboard([(author.id, author.name) for author in authors])
        if update.message:
            await update.message.reply_text(welcome_text, reply_markup=keyboard)

    async def author_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        author_id = int(query.data.split(":")[1])
        author = self._db.get_author(author_id)
        if not author:
            await query.edit_message_text("Не удалось найти сведения об авторе.")
            return

        text = (
            f"<b>{author.name}</b>\n\n"
            f"{author.short_bio}\n\n"
            "Выберите дальнейшее действие:"
        )

        await query.edit_message_text(
            text=text,
            reply_markup=author_menu_keyboard(author_id),
            parse_mode=ParseMode.HTML,
        )

    async def show_bio(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        author_id = int(query.data.split(":")[1])
        author = self._db.get_author(author_id)
        if not author:
            await query.edit_message_text("Биография недоступна.")
            return

        facts = "\n".join(f"• {item['year']}: {item['fact']}" for item in author.key_facts)
        text = (
            f"<b>{author.name}</b>\n\n"
            f"{author.bio}\n\n"
            "<b>Ключевые факты:</b>\n"
            f"{facts}"
        )

        await query.edit_message_text(
            text=text,
            reply_markup=back_to_menu_keyboard(author_id),
            parse_mode=ParseMode.HTML,
        )

    async def show_works(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        author_id = int(query.data.split(":")[1])
        author = self._db.get_author(author_id)
        if not author:
            await query.edit_message_text("Информация о произведениях недоступна.")
            return

        works = self._db.get_author_works(author_id)
        lines = [f"<b>Произведения {author.name}</b>"]
        for category, items in works.items():
            lines.append(f"\n<b>{category}</b>")
            for work in items:
                year = f" ({work['year']})" if work["year"] else ""
                lines.append(f"• {work['title']}{year} — {work['summary']}")
                if work.get("excerpt"):
                    lines.append(f"  <i>{work['excerpt']}</i>")

        await query.edit_message_text(
            text="\n".join(lines),
            reply_markup=back_to_menu_keyboard(author_id),
            parse_mode=ParseMode.HTML,
        )

    async def enter_dialog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        author_id = int(query.data.split(":")[1])
        author = self._db.get_author(author_id)
        if not author:
            await query.edit_message_text("Диалог недоступен: автор не найден.")
            return

        context.user_data["dialog_author_id"] = author_id
        context.user_data["dialog_author_name"] = author.name
        context.user_data["dialog_stage"] = "ask_name"
        context.user_data["poems_used"] = []

        await query.edit_message_text(
            text=(
                f"Вы вступили в беседу с {author.name}.\n\n"
                "Чтобы выйти, отправьте команду /stop или /menu."
            ),
            parse_mode=ParseMode.HTML,
        )
        if query.message:
            await query.message.reply_text(
                "Привет! Меня зовут Александр Сергеевич Пушкин! Как тебя зовут?"
            )

    async def handle_dialog_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        if not message:
            return

        text = message.text or ""
        text_lower = text.lower()

        author_id = context.user_data.get("dialog_author_id")
        if not author_id:
            await message.reply_text("Автор не выбран. Используйте /start.")
            return

        author = self._db.get_author(author_id)
        if not author:
            await message.reply_text("Не удалось загрузить сведения об авторе.")
            return

        stage = context.user_data.get("dialog_stage")

        if text_lower in {"привет", "здравствуй", "здравствуйте"} and stage != "ask_name":
            context.user_data["dialog_stage"] = "ask_name"
            context.user_data.setdefault("poems_used", [])
            await message.reply_text("Привет! Меня зовут Александр Сергеевич Пушкин! Как тебя зовут?")
            return

        if stage == "ask_name":
            cleaned = text.strip()
            if not cleaned:
                await message.reply_text("Не расслышал имени — повторите, пожалуйста.")
                return
            lower_cleaned = cleaned.lower()
            name_candidate = cleaned
            if "меня зовут" in lower_cleaned:
                start = lower_cleaned.find("меня зовут") + len("меня зовут")
                name_candidate = cleaned[start:].strip()
            elif lower_cleaned.startswith("меня"):
                parts = cleaned.split(maxsplit=2)
                if len(parts) >= 2:
                    name_candidate = parts[1]
            name_candidate = name_candidate.strip(" ,.!?;:\"'()[]{}<>«»—-")
            if not name_candidate:
                await message.reply_text("Давайте всё же представимся — как к вам обращаться?")
                return
            name = name_candidate.split()[0]
            context.user_data["user_name"] = name
            context.user_data["dialog_stage"] = "offer_poem"
            await message.reply_text(f"Привет, {name}! Хочешь, расскажу стих?")
            return

        if stage == "offer_poem":
            tokens = self._tokenize(text_lower)
            if tokens & {"нет", "неа"} or "не хочу" in text_lower or "не надо" in text_lower:
                await message.reply_text(
                    "Как скажешь! Но знай: мой стих всегда на изготовке, стоит лишь щёлкнуть веером."
                )
                return
            if any(
                phrase in text_lower
                for phrase in {"расскажи", "давай", "прочитай"}
            ) or tokens & {"да", "хочу", "конечно", "ага"}:
                if await self._send_random_poem(message, context, author):
                    context.user_data["dialog_stage"] = "after_poem"
                return

        if stage == "after_poem":
            if "ещё" in text_lower or "еще" in text_lower:
                if "расскажи" in text_lower or "прочитай" in text_lower or "стих" in text_lower:
                    if await self._send_random_poem(message, context, author):
                        context.user_data["dialog_stage"] = "after_poem"
                    return
            tokens = self._tokenize(text_lower)
            if tokens & {"нет", "хватит", "достаточно"} or "не надо" in text_lower:
                await message.reply_text(
                    "Хорошо, приберегу рифмы до лучшего случая. Но стоит вам мигнуть — и я снова в строю!"
                )
                return

        poem_answer = self._db.find_poem_text(author_id, text_lower)
        if poem_answer:
            await message.reply_text(poem_answer)
            return
        if "расскажи" in text_lower and "стих" in text_lower:
            poems_list = ", ".join(self._db.get_poem_titles(author_id))
            await message.reply_text(
                f"Могу рассказать стихи: {poems_list}. Уточните, какой вам нужен."
            )
            return

        character_answer = self._db.find_character_insight(author_id, text_lower)
        if character_answer:
            await message.reply_text(character_answer)
            return

        faq_answer = self._db.find_faq_answer(author_id, text_lower)
        if faq_answer:
            await message.reply_text(faq_answer)
            return

        works = self._db.get_author_works(author_id)
        ai_response = await self._ai.generate_reply(author, works, text)
        await message.reply_text(ai_response)

    async def back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        author_id = int(query.data.split(":")[1])
        author = self._db.get_author(author_id)
        if not author:
            await query.edit_message_text("Автор не найден.")
            return

        await query.edit_message_text(
            text=(
                f"<b>{author.name}</b>\n\n"
                f"{author.short_bio}\n\n"
                "Выберите дальнейшее действие:"
            ),
            reply_markup=author_menu_keyboard(author_id),
            parse_mode=ParseMode.HTML,
        )

    async def end(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("До новых встреч! Используйте /start, чтобы начать заново.")
        context.user_data.clear()

    async def stop_dialog(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keys = [
            "dialog_author_id",
            "dialog_author_name",
            "dialog_stage",
            "poems_used",
            "user_name",
        ]
        for key in keys:
            context.user_data.pop(key, None)
        if update.message:
            await update.message.reply_text("Диалог завершён. Используйте /start, чтобы начать заново.")

    async def _send_random_poem(self, message, context, author) -> bool:
        used = set(context.user_data.get("poems_used", []))
        poem = self._db.get_random_poem(author.id, used)
        if not poem:
            context.user_data["poems_used"] = []
            poem = self._db.get_random_poem(author.id)
            if not poem:
                await message.reply_text("Похоже, сейчас подходящих стихов под рукой нет.")
                return False
            used = set()
        context.user_data.setdefault("poems_used", []).append(poem["title"])
        await message.reply_text(f"{poem['title']}\n\n{poem['text']}")
        return True

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        separators = ",.!?;:\"'()[]{}<>«»—-"
        for char in separators:
            text = text.replace(char, " ")
        return {token for token in text.split() if token}

