import logging
import random
from typing import Tuple
from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram import Update, Bot

from models.phrase import Phrase

thumbs = [
    "https://cdn.20m.es/img2/recortes/2018/02/06/632781-600-338.jpg",
    "https://i.blogs.es/c60c05/quien-javier/450_1000.jpg",
    "https://media-cdn.tripadvisor.com/media/photo-s/0f/f9/86/eb/junto-a-mi-cunado-compartiendo.jpg",
    "https://img.elcomercio.pe/files/ec_article_videogalleria/uploads/2018/06/18/5b27a6c5c9c49.jpeg",
    "https://fotos.perfil.com/2016/10/26/1026claudiominnicellig.jpg",
    "https://www.ecestaticos.com/imagestatic/clipping/7f5/900/7f59009441d3cf042f374f50756f3c5b/tu-cunado-ese-que-dice-que-escribe.jpg?mtime=1456847457",
    "https://s4.eestatic.com/2017/05/05/reportajes/entrevistas/VOX-Santiago_Abascal-Entrevistas_213740088_33819883_1024x576.jpg",
    "https://i.ytimg.com/vi/NyOwsYAPzTE/hqdefault.jpg",
    "https://pbs.twimg.com/media/DFRYYkRXgAIGOjI.jpg",
    "http://www.eluniversalqueretaro.mx/sites/default/files/styles/f03-651x400/public/2018/04/06/q8-20.jpg.jpg?itok=G2zZUM1c",
    "https://static3.elcomercio.es/www/pre2017/multimedia/noticias/201703/26/media/22940314.jpg",
]

logger = logging.getLogger('cunhaobot')
BASE_TEMPLATE = '¿Que pasa, {}?'


def get_thumb():
    return random.choice(thumbs)


def random_combination(iterable: str, r: int) -> Tuple[str]:
    pool = tuple(iterable)
    n = len(pool)
    indices = sorted(random.sample(range(n), r))
    return tuple(pool[i] for i in indices)


def handle_inline_query(bot: Bot, update: Update):
    """Handle the inline query."""
    query = update.inline_query.query or '1'
    query_words = query.split(' ')
    size, finisher = int(query_words[0]), tuple(query_words[1:])

    phrases = Phrase.get_phrases()
    random.shuffle(phrases)
    size = size if size <= len(phrases) else len(phrases)
    combinations = set()

    for i in range(10):
        combination = random_combination(phrases, size)
        random.shuffle(phrases)
        combinations.add(combination if not finisher else combination + finisher)

    results = [InlineQueryResultArticle(
        id=uuid4(),
        title=', '.join(combination),
        input_message_content=InputTextMessageContent(
            BASE_TEMPLATE.format(', '.join(combination))
        ),
        thumb_url=get_thumb()
    ) for combination in combinations]

    random.shuffle(results)

    update.inline_query.answer(results, cache_time=1)
