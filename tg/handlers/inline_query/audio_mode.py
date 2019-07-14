import os
from typing import List

import boto3
from telegram import InlineQueryResultVoice, InlineQueryResultArticle

from utils import normalize_str
from utils.gcp import upload_audio, get_audio_url
from tg.text_router import get_query_mode, SHORT_MODE, LONG_MODE
from .short_mode import get_short_mode_results
from .long_mode import get_long_mode_results

AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY', '')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY', '')

polly_client = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name='eu-west-1').client('polly')


def short_result_to_audio_result(result: InlineQueryResultArticle) -> InlineQueryResultVoice:
    title = result.title
    clean_title = title.replace(',', '').replace(' ', '')
    audio_url = get_audio_url(clean_title)
    if not audio_url:
        words = result.input_message_content.message_text.split(',')
        intro = words.pop(0)
        emphatized_words = ','.join([
            f'<emphasis level="reduced"><prosody volume="loud">{word}</prosody></emphasis>'
            for word in words
        ])

        ssml_text = f'<speak>{intro}<amazon:breath duration="long" volume="x-loud"/>{emphatized_words}</speak>'

        speech = polly_client.synthesize_speech(VoiceId='Enrique',
                                                OutputFormat='ogg_vorbis',
                                                Text=ssml_text,
                                                TextType='ssml')
        audio_url = upload_audio(speech['AudioStream'].read(), clean_title)

    result_id = f"audio-{result.id}"
    return InlineQueryResultVoice(
        result_id[:63],
        audio_url,
        title,
    )


def long_result_to_audio_result(result: InlineQueryResultArticle) -> InlineQueryResultVoice:
    title = result.title
    audio_url = get_audio_url(title)
    if not audio_url:
        text = result.input_message_content.message_text
        speech = polly_client.synthesize_speech(VoiceId='Enrique',
                                                OutputFormat='ogg_vorbis',
                                                Text=text,)
        audio_url = upload_audio(speech['AudioStream'].read(), title)

    result_id = normalize_str(f"audio-{result.id}")
    return InlineQueryResultVoice(
        result_id[:63],
        audio_url,
        title,
    )


def get_audio_mode_results(input: str) -> List:
    mode, rest = get_query_mode(input)

    results = []
    if mode == SHORT_MODE:
        results = [short_result_to_audio_result(result) for result in get_short_mode_results(rest)[:5] if result.title]
    elif mode == LONG_MODE:
        results = [long_result_to_audio_result(result) for result in get_long_mode_results(rest)]

    return results
