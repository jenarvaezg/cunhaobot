import os
from typing import List
from uuid import uuid4

import boto3
from telegram import InlineQueryResultVoice

from handlers.inline_query.short_mode import get_short_mode_results
from utils.gcp import upload_audio, get_audio_url

AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY', '')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY', '')

polly_client = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name='eu-west-1').client('polly')


def get_audio_mode_results(input: str) -> List:
    short_results = get_short_mode_results(input)[:2]

    audio_results = []
    for result in short_results:
        title = result.title
        clean_title = title.replace(',', '').replace(' ', '')
        audio_url = get_audio_url(clean_title)
        if not audio_url:
            speech = polly_client.synthesize_speech(VoiceId='Enrique',
                                                    OutputFormat='ogg_vorbis',
                                                    Text=result.input_message_content.message_text)
            audio_url = upload_audio(speech['AudioStream'].read(), clean_title)

        audio_results.append(
            InlineQueryResultVoice(
                uuid4(),
                audio_url,
                title,
            )
        )

    return audio_results
