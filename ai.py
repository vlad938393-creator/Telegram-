from __future__ import annotations

import asyncio
from typing import Any

from openai import APIError, OpenAI

from .config import Settings
from .database import Author


class WriterAI:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = OpenAI(api_key=settings.openai_api_key)

    async def generate_reply(
        self,
        author: Author,
        works: dict[str, list[dict[str, Any]]],
        user_message: str,
    ) -> str:
        system_prompt = self._build_system_prompt(author, works)
        user_prompt = user_message.strip()

        try:
            response = await asyncio.to_thread(
                self._client.responses.create,
                model=self._settings.openai_model,
                input=[
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": system_prompt}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": user_prompt}],
                    },
                ],
                max_output_tokens=200,
            )
        except APIError as exc:
            code = getattr(exc, "code", None)
            return (
                "Не удалось связаться с литературной музой — сервер ответил ошибкой и оборвал беседу. "
                "Я уже готовлю перо к новой попытке, попробуйте написать ещё раз через минутку."
                f"{f' (код ошибки {code})' if code else ''}"
            )

        text = getattr(response, "output_text", "").strip()
        if text:
            return text
        return (
            "Я задумался так глубоко, что чернила застенчиво спрятались. "
            "Попробуйте переформулировать вопрос — и я отвечу с прежним пушкинским задором!"
        )

    def _build_system_prompt(self, author: Author, works: dict[str, list[dict[str, Any]]]) -> str:
        fact_lines = "\n".join(f"- {item['year']}: {item['fact']}" for item in author.key_facts)
        works_lines = []
        for category, items in works.items():
            works_lines.append(f"{category}:")
            for work in items:
                year = f" ({work['year']})" if work["year"] else ""
                works_lines.append(f"  • {work['title']}{year} — {work['summary']}")
                if work.get("excerpt"):
                    works_lines.append(f"    Цитата: «{work['excerpt']}»")
        works_block = "\n".join(works_lines)

        return (
            f"{author.style_description}\n\n"
            f"Главные факты биографии:\n{fact_lines}\n\n"
            f"Краткая биографическая справка: {author.bio}\n\n"
            f"Произведения для упоминания:\n{works_block}\n\n"
            "Отвечай как живой Пушкин, но не выдавай вымыслы, если их нет в фактах. "
            "Поддерживай диалог, задавая встречные вопросы, когда уместно. "
            "Сохраняй уважительный тон, не отклоняйся от исторического контекста XIX века."
        )

