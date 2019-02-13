from google.cloud import datastore


class Phrase:
    kind = 'Phrase'

    phrases_cache = []

    def __init__(self, text):
        self.text = text

    @classmethod
    def upload_from_proposal(cls, proposal):
        phrase = Phrase(proposal.text)
        datastore_client = datastore.Client()
        key = datastore_client.key(cls.kind, phrase.text)
        phrase_entity = datastore.Entity(key=key)

        phrase_entity['text'] = phrase.text

        datastore_client.put(phrase_entity)
        cls.phrases_cache.append(phrase)

    @classmethod
    def from_entity(cls, entity):
        return cls(
            entity['text']
        )

    @classmethod
    def get_phrases(cls):
        if len(cls.phrases_cache) == 0:
            datastore_client = datastore.Client()
            query = datastore_client.query(kind=cls.kind)
            cls.phrases_cache = [cls.from_entity(entity) for entity in query.fetch()]

        return cls.phrases_cache



