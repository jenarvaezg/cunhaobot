import unittest

from tg.handlers.inline_query.base import get_query_mode, SHORT_MODE, SHORT_MODE_WORDS, LONG_MODE_WORDS, LONG_MODE, \
    AUDIO_MODE_WORDS, AUDIO_MODE


class TestGetQueryMode(unittest.TestCase):
    def test_empty(self):
        query = ''
        expected = SHORT_MODE, ''

        actual = get_query_mode(query)

        self.assertEqual(actual, expected)

    def test_only_number(self):
        query = '1'
        expected = SHORT_MODE, '1'

        actual = get_query_mode(query)

        self.assertEqual(actual, expected)

    def test_only_number_and_whitespace(self):
        query = '  1  '
        expected = SHORT_MODE, '1'

        actual = get_query_mode(query)

        self.assertEqual(expected, actual)

    def test_number_and_finisher(self):
        query = '10 this is a test'
        expected = SHORT_MODE, '10 this is a test'

        actual = get_query_mode(query)

        self.assertEqual(expected, actual)

    def test_short_word_number_and_finisher(self):
        query = f'{SHORT_MODE_WORDS[0]} 10 this is a test'
        expected = SHORT_MODE, '10 this is a test'

        actual = get_query_mode(query)

        self.assertEqual(expected, actual)

    def test_long_word(self):
        query = f'{LONG_MODE_WORDS[0]} whatever this is not defined yet'
        expected = LONG_MODE, 'whatever this is not defined yet'

        actual = get_query_mode(query)

        self.assertEqual(expected, actual)

    def test_audio_word(self):
        query = f'{AUDIO_MODE_WORDS[0]} whatever this is not defined yet'
        expected = AUDIO_MODE, 'whatever this is not defined yet'

        actual = get_query_mode(query)

        self.assertEqual(expected, actual)

    def test_gibberish(self):
        query = 'dhnjdka'
        expected = '', ''

        actual = get_query_mode(query)

        self.assertEqual(expected, actual)
