from models.phrase import Phrase, LongPhrase


class TestPhrase:
    def test_phrase_init(self):
        p = Phrase(text="hola")
        assert p.text == "hola"
        assert p.usages == 0

    def test_phrase_str(self):
        p = Phrase(text="hola")
        assert str(p) == "hola"

    def test_phrase_eq(self):
        p1 = Phrase(text="foo")
        p2 = Phrase(text="foo")
        p3 = Phrase(text="bar")
        assert p1 == p2
        assert p1 != p3
        assert p1 != "foo"


class TestLongPhrase:
    def test_long_phrase_init(self):
        lp = LongPhrase(text="hola mundo")
        assert lp.text == "hola mundo"
        assert lp.kind == "LongPhrase"
