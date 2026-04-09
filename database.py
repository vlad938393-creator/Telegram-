from __future__ import annotations

import json
import random
import sqlite3
import threading
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional


@dataclass
class Author:
    id: int
    name: str
    short_bio: str
    bio: str
    era: str
    key_facts: list[dict[str, str]]
    style_description: str


@dataclass
class Character:
    id: int
    author_id: int
    name: str
    description: str
    keywords: list[str]


@dataclass
class Poem:
    id: int
    author_id: int
    title: str
    text: str
    keywords: list[str]


class Database:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        self._init_schema()
        self._seed_pushkin()

    @contextmanager
    def _cursor(self) -> Iterator[sqlite3.Cursor]:
        with self._lock:
            cursor = self._conn.cursor()
            try:
                yield cursor
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                cursor.close()

    def _init_schema(self) -> None:
        with self._cursor() as cur:
            cur.executescript(
                """
                CREATE TABLE IF NOT EXISTS authors (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    short_bio TEXT NOT NULL,
                    bio TEXT NOT NULL,
                    era TEXT NOT NULL,
                    key_facts TEXT NOT NULL,
                    style_description TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY,
                    author_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    year INTEGER,
                    category TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    excerpt TEXT,
                    FOREIGN KEY (author_id) REFERENCES authors(id)
                );

                CREATE TABLE IF NOT EXISTS faq (
                    id INTEGER PRIMARY KEY,
                    author_id INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    FOREIGN KEY (author_id) REFERENCES authors(id)
                );

                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY,
                    author_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    FOREIGN KEY (author_id) REFERENCES authors(id)
                );

                CREATE TABLE IF NOT EXISTS poems (
                    id INTEGER PRIMARY KEY,
                    author_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    FOREIGN KEY (author_id) REFERENCES authors(id)
                );
                """
            )

    def _seed_pushkin(self) -> None:
        with self._cursor() as cur:
            cur.execute("SELECT id FROM authors WHERE name = ?", ("Александр Сергеевич Пушкин",))
            row = cur.fetchone()
            if row:
                author_id = row["id"]
            else:
                key_facts = [
                    {"year": "1799", "fact": "Родился в Москве в дворянской семье."},
                    {"year": "1811–1817", "fact": "Учился в Царскосельском лицее, где начал писать стихи."},
                    {"year": "1820", "fact": "Сослан на юг за политические стихотворения."},
                    {"year": "1824", "fact": "Сослан в Михайловское, где создал множество лирических произведений."},
                    {"year": "1831", "fact": "Женился на Наталье Гончаровой; сблизился с кружком Гоголя."},
                    {"year": "1837", "fact": "Погиб на дуэли с Жоржем Дантесом, защищая честь семьи."},
                ]

                style_description = (
                    "Ты — Александр Сергеевич Пушкин, классик русской литературы, остроумный, живой, благородный. "
                    "Отвечай с лёгкой ироничностью и теплом, вплетай культурные отсылки, но опирайся на факты биографии, "
                    "историю России XIX века и содержание собственных произведений. Говори уверенно, метафорично, "
                    "не злоупотребляй архаизмами, но допускай пушкинский шарм."
                )

                cur.execute(
                    """
                    INSERT INTO authors (name, short_bio, bio, era, key_facts, style_description)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "Александр Сергеевич Пушкин",
                        "Русский поэт, драматург и прозаик, основоположник современного русского литературного языка.",
                        (
                            "Александр Сергеевич Пушкин (1799–1837) — русский поэт, драматург и прозаик, создатель "
                            "современного русского литературного языка. Выпускник Царскосельского лицея, он рано привлёк "
                            "внимание стихами «вольнолюбивого содержания» и был отправлен в ссылку на юг, затем в Михайловское. "
                            "Через исторические сюжеты, романтические поэмы и реалистическую прозу Пушкин создал панораму "
                            "русской жизни и человеческих характеров. Его ключевые произведения — «Евгений Онегин», «Медный всадник», "
                            "«Борис Годунов», «Повести Белкина», «Капитанская дочка». Погиб на дуэли, став символом трагической судьбы творца."
                        ),
                        "Золотой век русской литературы",
                        json.dumps(key_facts, ensure_ascii=False),
                        style_description,
                    ),
                )

                author_id = cur.lastrowid

            works: list[tuple[str, Optional[int], str, str, Optional[str]]] = [
                ("Няне", 1826, "Стихи", "Посвящение Арине Родионовне, проникнутое нежностью и благодарностью.", None),
                ("Узник", 1822, "Стихи", "Лирическое размышление о жажде свободы заключённого.", None),
                ("Я вас любил: любовь ещё, быть может", 1829, "Стихи", "Признание в глубоком, но безответном чувстве, сказанное с деликатностью.", None),
                ("Осень", 1833, "Стихи", "Размышление о вдохновении и ясности мысли, приходящих с осеней порой.", None),
                ("Кавказ", 1829, "Стихи", "Поэтический отклик на величие Кавказа и романтику свободы.", None),
                ("У лукоморья дуб зелёный", 1820, "Стихи", "Пролог к «Руслану и Людмиле», полный волшебных образов.", None),
                ("Я помню чудное мгновенье", 1825, "Стихи", "Воспоминание о встрече, оживляющее чувства и надежды.", None),
                ("Зимнее утро", 1829, "Стихи", "Восторженное описание сияющего русского зимнего утра.", None),
                ("Руслан и Людмила", 1820, "Поэмы", "Романтическая поэма, прославляющая силу любви и смелости.", None),
                ("Кавказский пленник", 1821, "Поэмы", "Романтическая поэма о свободе и внутреннем перерождении.", None),
                ("Бахчисарайский фонтан", 1823, "Поэмы", "Поэма о трагической любви крымского хана Гирея.", None),
                ("Цыганы", 1824, "Поэмы", "Поэма о столкновении свободы и ревности.", None),
                ("Полтава", 1828, "Поэмы", "Историческая поэма о судьбе Мазепы и Полтавской битве.", None),
                ("Медный всадник", 1833, "Поэмы", "Поэма о противостоянии маленького человека и государственной стихии.", "Люблю тебя, Петра творенье..."),
                ("Евгений Онегин", 1833, "Романы", "Роман в стихах о судьбах молодого дворянина и Татьяны Лариной.", "Мой дядя самых честных правил..."),
                ("Капитанская дочка", 1836, "Романы", "Историческая повесть о восстании Пугачёва и взрослении Петра Гринева.", None),
                ("Повести Белкина", 1831, "Повести", "Цикл повестей, раскрывающих разные грани человеческого характера.", None),
                ("Петербургская повесть", 1833, "Повести", "Повесть «Пиковая дама» о судьбе Германа и тайне трёх карт.", None),
                ("Борис Годунов", 1825, "Драмы", "Историческая трагедия о власти, совести и народе.", None),
                ("Маленькие трагедии", 1830, "Драмы", "Цикл драматических сцен о страстях и неминуемой расплате.", None),
                ("Сказка о царе Салтане", 1831, "Сказки", "Поэтическая сказка о чудесах, верности и награде за терпение.", None),
                ("Сказка о мёртвой царевне и о семи богатырях", 1833, "Сказки", "Сказка о зависти и чистоте сердца.", None),
            ]

            for title, year, category, summary, excerpt in works:
                self._ensure_book(cur, author_id, title, year, category, summary, excerpt)

            faq_entries = [
                (
                    "Используете план или пишете интуитивно, позволяя сюжету развиваться естественным образом?",
                    "Чаще всего я приступаю к россказню, наметив сдержанный план, а потом позволяю героям и самой жизни "
                    "вмешиваться. Каркас необходим, но истинное очарование рождается, когда сюжет вдруг расправляет свои "
                    "крылья и ведёт меня туда, куда не ожидал.",
                    ["план", "интуитивно", "сюжет"],
                ),
                (
                    "Сталкиваетесь ли вы с писательским блоком? Как справляетесь с ним?",
                    "И случалось и со мной томиться в сухой земле вдохновения. В такие дни я ищу живое впечатление: беседу, "
                    "дорогу, письмо друга. Иногда спасает чтение чужих строк — дух соперничества будит перо.",
                    ["писательский", "блок", "вдохновение"],
                ),
                (
                    "В какое время суток предпочитаете писать?",
                    "Лучшие строки приходят ранним утром, когда Петербург ещё дремлет, либо ближе к ночи, когда мысли "
                    "обретают свободу. Но в сущности, вдохновение не признаёт расписаний.",
                    ["время", "суток", "когда пишете", "утро", "ночь"],
                ),
                (
                    "Что делаете с законченным черновиком: сразу редактируете или даёте тексту отлежаться?",
                    "Черновик я оставляю дозревать. Лишь спустя время взгляд становится беспристрастным, и тогда можно "
                    "без жалости вычеркнуть лишнее, украсить нужное.",
                    ["черновик", "редактируете", "отлежаться"],
                ),
                (
                    "Есть ли случаи из жизни, которые вдохновили на конкретные сюжеты?",
                    "Разумеется! «Капитанская дочка» выросла из рассказов о Пугачёвском бунте, «Пиковая дама» — из петербургских "
                    "анекдотов о картёжниках. Жизнь — мой главный соавтор.",
                    ["случаи", "жизни", "сюжеты", "вдохновили"],
                ),
                (
                    "Как работаете над характерами героев, часто ли персонажи основаны на реальных людях?",
                    "Я внимательно слушаю людей, встречаю их в салонах, на дорогах, в письмах. Герои — собрание реальных "
                    "наблюдений и поэтических домыслов. Например, Татьяну я писал, вспоминая умных и гордых дворянок.",
                    ["характер", "героев", "персонажи", "реальных"],
                ),
                (
                    "Есть ли любимый персонаж из собственных книг? Кто он и почему так близок?",
                    "Мне близок Татьянин образ — цельная, верная натура. Однако и облагораживающийся Гринёв, и ироничный "
                    "Онегин дороги по-своему: они живут настоящей жизнью.",
                    ["любимый персонаж", "кто он"],
                ),
                (
                    "Если бы вы не стали писателем, какую деятельность выбрали бы?",
                    "Думаю, служил бы отечеству пером дипломатическим либо историческим. История России меня всегда "
                    "занимала не меньше поэзии.",
                    ["если бы не", "писателем", "деятельность"],
                ),
                (
                    "Как реагируете на критику читателей?",
                    "Критика полезна, когда умна и сердечна. Я привык слушать друзей — Жуковского, Гоголя, Плетнёва. "
                    "А вот злобная брань лишь подтверждает: попал в живую точку.",
                    ["критика", "читателей", "реагируете"],
                ),
                (
                    "Есть ли у вас творческая мечта, чего хотелось бы достичь?",
                    "Мне хотелось бы, чтобы русский язык звучал свободно и ясно, чтобы мои герои помогали современникам "
                    "вспоминать о чести, любви и свободе. В этом и есть моя творческая мечта.",
                    ["творческая мечта", "достичь"],
                ),
                (
                    "Как вы умерли?",
                    "Я пал на дуэли 29 января (10 февраля) 1837 года, защищая честь жены и семьи. Пуля Дантеса стала "
                    "последней страницей моей земной биографии, но слово осталось жить.",
                    ["как умер", "дуэль", "дантес"],
                ),
            ]

            for question, answer, keywords in faq_entries:
                self._ensure_faq(cur, author_id, question, answer, keywords)

            characters = [
                (
                    "Татьяна Ларина",
                    "Героиня «Евгения Онегина»: цельная, мечтательная, воспитанная на романах, но глубоко честная и верная своим принципам.",
                    ["татьяна", "ларина", "татьяны"],
                ),
                (
                    "Евгений Онегин",
                    "Столичный дворянин, образованный скептик, который слишком рано разочаровался и упустил любовь Татьяны.",
                    ["онегин", "евгений онегин"],
                ),
                (
                    "Владимир Ленский",
                    "Молодой поэт-романтик, искренний и восторженный, противопоставление Онегину; погибает на дуэли.",
                    ["ленский", "владимир ленский"],
                ),
                (
                    "Пётр Гринёв",
                    "Главный герой «Капитанской дочки»: честный дворянин, проходящий путь взросления и сохраняющий честь в смутное время.",
                    ["гринев", "пётр гринёв", "петр гринев"],
                ),
                (
                    "Мария Миронова",
                    "Невеста Гринева: кроткая, верная и смелая девушка, воплощающая нравственный идеал.",
                    ["мария миронова", "маша миронова", "марья миронова"],
                ),
                (
                    "Германн",
                    "Антигерой «Пиковой дамы»: рациональный офицер, одержимый идеей разбогатеть, что приводит его к безумию.",
                    ["герман", "германн", "германа"],
                ),
                (
                    "Руслан",
                    "Отважный витязь из поэмы «Руслан и Людмила», символ верности и храбрости.",
                    ["руслан"],
                ),
                (
                    "Людмила",
                    "Красавица из «Руслана и Людмилы», чья преданность помогает герою победить.",
                    ["людмила"],
                ),
            ]

            for name, description, keywords in characters:
                self._ensure_character(cur, author_id, name, description, keywords)

            poems = [
                (
                    "Няне",
                    "Подруга дней моих суровых,\n"
                    "Голубка дряхлая моя!\n"
                    "Одна в глуши лесов сосновых\n"
                    "Давно, давно ты ждёшь меня.\n\n"
                    "Ты под окном своей светлицы\n"
                    "Горюешь будто на часах,\n"
                    "И медлят поминутно спицы\n"
                    "В твоих наморщенных руках.\n\n"
                    "Глядишь в забытые вороты\n"
                    "На чёрный отдалённый путь:\n"
                    "Тоска, предчувствия, заботы\n"
                    "Теснят твою всечасно грудь.\n\n"
                    "То чудится тебе... (продолжение стихотворения можно найти в полном издании).",
                    ["няне", "няню", "стих няне", "расскажи стих няне"],
                ),
                (
                    "Узник",
                    "Сижу за решёткой в темнице сырой.\n"
                    "Вскормлённый в неволе орёл молодой,\n"
                    "Мой грустный товарищ, махая крылом,\n"
                    "Кровавую пищу клюёт под окном.\n\n"
                    "Кровавую пищу клюёт под окном,\n"
                    "Мой грустный товарищ, махая крылом;\n"
                    "Вскормлённый в неволе орёл молодой,\n"
                    "Сижу за решёткой в темнице сырой.\n\n"
                    "Мы вольные птицы; пора, брат, пора!\n"
                    "Туда, где за тучей белеет гора,\n"
                    "Туда, где синеют морские края,\n"
                    "Туда, где гуляем лишь ветер... да я!",
                    ["узник", "стих узник", "расскажи стих узник"],
                ),
                (
                    "Я вас любил: любовь ещё, быть может",
                    (
                        "Я вас любил: любовь ещё, быть может,\n"
                        "В душе моей угасла не совсем;\n"
                        "Но пусть она вас больше не тревожит;\n"
                        "Я не хочу печалить вас ничем.\n\n"
                        "Я вас любил безмолвно, безнадежно,\n"
                        "То робостью, то ревностью томим;\n"
                        "Я вас любил так искренно, так нежно,\n"
                        "Как дай вам Бог любимой быть другим."
                    ),
                    [
                        "я вас любил",
                        "любовь еще",
                        "стих я вас любил",
                        "расскажи стих я вас любил",
                    ],
                ),
                (
                    "Осень",
                    (
                        "Унылая пора! Очей очарованье!\n"
                        "Приятна мне твоя прощальная краса —\n"
                        "Люблю я пышное природы увяданье,\n"
                        "В багрец и в золото одетые леса.\n\n"
                        "В их сенях ветра шум и свежее дыханье,\n"
                        "И мглой волнистою покрыты небеса,\n"
                        "И редкий солнечный денёк, и первые морозы,\n"
                        "И отдалённые седой зимы угрозы."
                    ),
                    ["осень", "стих осень", "расскажи стих осень"],
                ),
                (
                    "Кавказ",
                    "На холмах Грузии лежит ночная мгла;\n"
                    "Шумит Арагва предо мной.\n"
                    "Мне грустно и легко; печаль моя светла;\n"
                    "Печаль моя полна тобой.\n\n"
                    "Она тобой, одной тобой согрета,\n"
                    "И сердце вновь горит и любит — оттого,\n"
                    "Что не любить оно не может,\n"
                    "Как в прошлом, как любило вновь и снова.",
                    ["кавказ", "стих кавказ", "расскажи стих кавказ"],
                ),
                (
                    "У лукоморья дуб зелёный",
                    "У лукоморья дуб зелёный;\n"
                    "Златая цепь на дубе том:\n"
                    "И днём и ночью кот учёный\n"
                    "Всё ходит по цепи кругом;\n\n"
                    "Идёт направо — песнь заводит,\n"
                    "Налево — сказку говорит.\n"
                    "Там чудеса: там леший бродит,\n"
                    "Русалка на ветвях сидит...",
                    [
                        "у лукоморья",
                        "дуб зеленый",
                        "стих у лукоморья",
                        "расскажи стих у лукоморья",
                    ],
                ),
                (
                    "Я помню чудное мгновенье",
                    "Я помню чудное мгновенье:\n"
                    "Передо мной явилась ты,\n"
                    "Как мимолётное виденье,\n"
                    "Как гений чистой красоты.\n\n"
                    "В томленьях грусти безнадёжной,\n"
                    "В тревогах шумной суеты,\n"
                    "Звучал мне долго голос нежный\n"
                    "И снились милые черты.\n\n"
                    "Шли годы. Бурь порыв мятежный\n"
                    "Рассеял прежние мечты,\n"
                    "И я забыл твой голос нежный,\n"
                    "Твои небесные черты.\n\n"
                    "В глуши, во мраке заточенья\n"
                    "Тянулись тихо дни мои\n"
                    "Без божества, без вдохновенья,\n"
                    "Без слёз, без жизни, без любви.\n\n"
                    "Душе настало пробужденье:\n"
                    "И вот опять явилась ты,\n"
                    "Как мимолётное виденье,\n"
                    "Как гений чистой красоты.\n\n"
                    "И сердце бьётся в упоенье,\n"
                    "И для него воскресли вновь\n"
                    "И божество, и вдохновенье,\n"
                    "И жизнь, и слёзы, и любовь.",
                    [
                        "я помню чудное",
                        "чудное мгновенье",
                        "расскажи стих я помню чудное",
                    ],
                ),
                (
                    "Зимнее утро",
                    "Мороз и солнце; день чудесный!\n"
                    "Ещё ты дремлешь, друг прелестный —\n"
                    "Пора, красавица, проснись:\n"
                    "Открой сомкнуты негой взоры\n"
                    "Навстречу северной Авроры,\n"
                    "Звездою севера явись!\n\n"
                    "Вечор, ты помнишь, вьюга злилась,\n"
                    "На мутном небе мгла носилась;\n"
                    "Луна, как бледное пятно,\n"
                    "Сквозь тучи мрачные желтела,\n"
                    "И ты печальная сидела —\n"
                    "А нынче... погляди в окно!",
                    [
                        "зимнее утро",
                        "стих зимнее утро",
                        "расскажи стих зимнее утро",
                    ],
                ),
            ]

            for title, text, keywords in poems:
                self._ensure_poem(cur, author_id, title, text, keywords)

    def _ensure_book(
        self,
        cur: sqlite3.Cursor,
        author_id: int,
        title: str,
        year: Optional[int],
        category: str,
        summary: str,
        excerpt: Optional[str],
    ) -> None:
        cur.execute(
            "SELECT 1 FROM books WHERE author_id = ? AND title = ?",
            (author_id, title),
        )
        if cur.fetchone():
            cur.execute(
                """
                UPDATE books
                SET year = ?, category = ?, summary = ?, excerpt = ?
                WHERE author_id = ? AND title = ?
                """,
                (year, category, summary, excerpt, author_id, title),
            )
        else:
            cur.execute(
                """
                INSERT INTO books (author_id, title, year, category, summary, excerpt)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (author_id, title, year, category, summary, excerpt),
            )

    def _ensure_faq(
        self,
        cur: sqlite3.Cursor,
        author_id: int,
        question: str,
        answer: str,
        keywords: list[str],
    ) -> None:
        normalized_keywords = [kw.lower() for kw in keywords]
        cur.execute(
            "SELECT 1 FROM faq WHERE author_id = ? AND question = ?",
            (author_id, question),
        )
        if cur.fetchone():
            cur.execute(
                """
                UPDATE faq
                SET answer = ?, keywords = ?
                WHERE author_id = ? AND question = ?
                """,
                (answer, json.dumps(normalized_keywords, ensure_ascii=False), author_id, question),
            )
        else:
            cur.execute(
                """
                INSERT INTO faq (author_id, question, answer, keywords)
                VALUES (?, ?, ?, ?)
                """,
                (author_id, question, answer, json.dumps(normalized_keywords, ensure_ascii=False)),
            )

    def _ensure_character(
        self,
        cur: sqlite3.Cursor,
        author_id: int,
        name: str,
        description: str,
        keywords: list[str],
    ) -> None:
        normalized_keywords = [kw.lower() for kw in keywords]
        cur.execute(
            "SELECT 1 FROM characters WHERE author_id = ? AND name = ?",
            (author_id, name),
        )
        if cur.fetchone():
            cur.execute(
                """
                UPDATE characters
                SET description = ?, keywords = ?
                WHERE author_id = ? AND name = ?
                """,
                (description, json.dumps(normalized_keywords, ensure_ascii=False), author_id, name),
            )
        else:
            cur.execute(
                """
                INSERT INTO characters (author_id, name, description, keywords)
                VALUES (?, ?, ?, ?)
                """,
                (author_id, name, description, json.dumps(normalized_keywords, ensure_ascii=False)),
            )

    def _ensure_poem(
        self,
        cur: sqlite3.Cursor,
        author_id: int,
        title: str,
        text: str,
        keywords: list[str],
    ) -> None:
        normalized_keywords = [kw.lower() for kw in keywords]
        cur.execute(
            "SELECT 1 FROM poems WHERE author_id = ? AND title = ?",
            (author_id, title),
        )
        if cur.fetchone():
            cur.execute(
                """
                UPDATE poems
                SET text = ?, keywords = ?
                WHERE author_id = ? AND title = ?
                """,
                (text, json.dumps(normalized_keywords, ensure_ascii=False), author_id, title),
            )
        else:
            cur.execute(
                """
                INSERT INTO poems (author_id, title, text, keywords)
                VALUES (?, ?, ?, ?)
                """,
                (author_id, title, text, json.dumps(normalized_keywords, ensure_ascii=False)),
            )

    def get_author(self, author_id: int) -> Optional[Author]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id, name, short_bio, bio, era, key_facts, style_description FROM authors WHERE id = ?",
                (author_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            return Author(
                id=row["id"],
                name=row["name"],
                short_bio=row["short_bio"],
                bio=row["bio"],
                era=row["era"],
                key_facts=json.loads(row["key_facts"]),
                style_description=row["style_description"],
            )

    def get_author_by_name(self, name: str) -> Optional[Author]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id FROM authors WHERE name = ?",
                (name,),
            )
            row = cur.fetchone()
            if not row:
                return None
        return self.get_author(row["id"])

    def get_author_works(self, author_id: int) -> dict[str, list[dict[str, Any]]]:
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT title, year, category, summary, excerpt
                FROM books
                WHERE author_id = ?
                ORDER BY
                    CASE category
                        WHEN 'Стихи' THEN 1
                        WHEN 'Поэмы' THEN 2
                        WHEN 'Романы' THEN 3
                        WHEN 'Повести' THEN 4
                        WHEN 'Драмы' THEN 5
                        WHEN 'Сказки' THEN 6
                        ELSE 99
                    END,
                    year IS NULL,
                    year,
                    title
                """,
                (author_id,),
            )
            rows = cur.fetchall()

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["category"]].append(
                {
                    "title": row["title"],
                    "year": row["year"],
                    "summary": row["summary"],
                    "excerpt": row["excerpt"],
                }
            )
        return grouped

    def get_faq_entries(self, author_id: int) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT question, answer, keywords FROM faq WHERE author_id = ?",
                (author_id,),
            )
            rows = cur.fetchall()

        return [
            {
                "question": row["question"],
                "answer": row["answer"],
                "keywords": json.loads(row["keywords"]),
            }
            for row in rows
        ]

    def find_faq_answer(self, author_id: int, user_text: str) -> Optional[str]:
        normalized = user_text.lower()
        for entry in self.get_faq_entries(author_id):
            if any(keyword in normalized for keyword in entry["keywords"]):
                return entry["answer"]
        return None

    def find_poem_text(self, author_id: int, user_text: str) -> Optional[str]:
        normalized = user_text.lower()
        with self._cursor() as cur:
            cur.execute(
                "SELECT title, text, keywords FROM poems WHERE author_id = ?",
                (author_id,),
            )
            rows = cur.fetchall()

        for row in rows:
            keywords = json.loads(row["keywords"])
            if any(keyword in normalized for keyword in keywords):
                return f"{row['title']}\n\n{row['text']}"
        return None

    def get_poem_titles(self, author_id: int) -> list[str]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT title FROM poems WHERE author_id = ? ORDER BY title",
                (author_id,),
            )
            rows = cur.fetchall()
        return [row["title"] for row in rows]

    def get_random_poem(
        self,
        author_id: int,
        exclude_titles: Optional[set[str]] = None,
    ) -> Optional[dict[str, str]]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT title, text FROM poems WHERE author_id = ?",
                (author_id,),
            )
            rows = cur.fetchall()

        candidates = [
            {"title": row["title"], "text": row["text"]}
            for row in rows
            if not exclude_titles or row["title"] not in exclude_titles
        ]
        if not candidates:
            return None
        return random.choice(candidates)

    def find_character_insight(self, author_id: int, user_text: str) -> Optional[str]:
        normalized = user_text.lower()
        with self._cursor() as cur:
            cur.execute(
                "SELECT name, description, keywords FROM characters WHERE author_id = ?",
                (author_id,),
            )
            rows = cur.fetchall()

        for row in rows:
            keywords = json.loads(row["keywords"])
            if any(keyword in normalized for keyword in keywords):
                return f"{row['name']}: {row['description']}"
        return None

    def list_authors(self) -> list[Author]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id, name, short_bio, bio, era, key_facts, style_description FROM authors ORDER BY name"
            )
            rows = cur.fetchall()

        return [
            Author(
                id=row["id"],
                name=row["name"],
                short_bio=row["short_bio"],
                bio=row["bio"],
                era=row["era"],
                key_facts=json.loads(row["key_facts"]),
                style_description=row["style_description"],
            )
            for row in rows
        ]

    def close(self) -> None:
        with self._lock:
            self._conn.close()

