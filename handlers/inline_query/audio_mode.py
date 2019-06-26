import os
from typing import List

import boto3
from telegram import InlineQueryResultVoice, InlineQueryResultArticle

from handlers.inline_query.short_mode import get_short_mode_results
from handlers.inline_query.long_mode import  get_long_mode_results
from utils.gcp import upload_audio, get_audio_url

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

    return InlineQueryResultVoice(
        f'audio-{result.id}',
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

    return InlineQueryResultVoice(
        f'audio-{result.id}',
        audio_url,
        title,
    )


def get_audio_mode_results(input: str) -> List:
    if input.startswith('search'):
        short_results = []
        long_results = get_long_mode_results(input)[:10]
    else:
        short_results = get_short_mode_results(input)[:4]
        long_results = get_long_mode_results(input)[:6]

    short_audio_results = [short_result_to_audio_result(short_result) for short_result in short_results]
    long_audio_results = [long_result_to_audio_result(long_result) for long_result in long_results]

    return short_audio_results + long_audio_results
