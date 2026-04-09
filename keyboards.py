from __future__ import annotations

from typing import Iterable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def author_selection_keyboard(authors: Iterable[tuple[int, str]]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"author:{author_id}")]
        for author_id, name in authors
    ]
    return InlineKeyboardMarkup(buttons)


def author_menu_keyboard(author_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("📖 Биография", callback_data=f"bio:{author_id}"),
            InlineKeyboardButton("📚 Произведения", callback_data=f"works:{author_id}"),
        ],
        [
            InlineKeyboardButton("💬 Диалог", callback_data=f"dialog:{author_id}"),
            InlineKeyboardButton("⏹ Завершить", callback_data="end"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def back_to_menu_keyboard(author_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Назад", callback_data=f"menu:{author_id}")]]
    )

