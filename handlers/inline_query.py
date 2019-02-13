import itertools
import random
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
]


def get_thumb():
    return random.choice(thumbs)


def handle_inline_query(bot: Bot, update: Update):
    """Handle the inline query."""
    query = update.inline_query.query or '1'
    size = int(query)
    base_template = '¿Que pasa, {}?'

    phrases = Phrase.get_phrases()
    random.shuffle(phrases)
    combinations = itertools.combinations(phrases, size if size <= len(phrases) else len(phrases))

    results = [InlineQueryResultArticle(
                id=uuid4(),
                title=', '.join([phrase.text for phrase in combination]),
                input_message_content=InputTextMessageContent(
                    base_template.format(', '.join([phrase.text for phrase in combination]))
                ),
                thumb_url=get_thumb()
            ) for combination in combinations]

    random.shuffle(results)
    if len(results) > 50:
        results = results[:50]

    update.inline_query.answer(results, cache_time=1)
