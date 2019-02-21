from google.cloud import datastore

from models.phrase import Phrase, LongPhrase


class Proposal:
    kind = 'Proposal'
    phrase_class = Phrase

    @staticmethod
    def proposal_text_from_update(update):
        return " ".join(update.message.text.split(" ")[1:]).strip()

    def __init__(self, id, from_chat_id, from_message_id, text, likes=0, dislikes=0, voted_by=[]):
        self.id = id
        self.from_chat_id = from_chat_id
        self.from_message_id = from_message_id
        self.text = text
        self.likes = likes
        self.dislikes = dislikes
        self.voted_by = voted_by

    @classmethod
    def from_update(cls, update):
        id = str(update.message.chat.id + update.message.message_id)
        return cls(id, update.message.chat.id, update.message.message_id, cls.proposal_text_from_update(update))

    @classmethod
    def load(cls, id):
        datastore_client = datastore.Client()
        key = datastore_client.key(cls.kind, id)

        entity = datastore_client.get(key)
        if entity is None:
            return entity

        return cls(
            entity.key.name,
            entity['from_chat_id'],
            entity['from_message_id'],
            entity['text'],
            entity['likes'],
            entity['dislikes'],
            entity['voted_by']
        )

    def save(self):
        datastore_client = datastore.Client()
        key = datastore_client.key(self.kind, self.id)
        proposal_entity = datastore.Entity(key=key)

        proposal_entity['text'] = self.text
        proposal_entity['likes'] = self.likes
        proposal_entity['dislikes'] = self.dislikes
        proposal_entity['from_chat_id'] = self.from_chat_id
        proposal_entity['from_message_id'] = self.from_message_id
        proposal_entity['voted_by'] = self.voted_by

        datastore_client.put(proposal_entity)

    def add_vote(self, positive, voter_id):
        if positive:
            self.likes += 1
        else:
            self.dislikes += 1

        self.voted_by.append(voter_id)


class LongProposal(Proposal):
    kind = 'LongProposal'
    phrase_class = LongPhrase


def get_proposal_class_by_kind(kind: str) -> Proposal:
    if kind == LongProposal.kind:
        return LongProposal

    return Proposal
