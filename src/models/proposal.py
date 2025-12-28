from typing import Optional

from google.cloud import datastore
from telegram import Message, Update

from models.phrase import LongPhrase, Phrase


class Proposal:
    kind = "Proposal"
    phrase_class: type[Phrase] = Phrase

    @staticmethod
    def proposal_text_from_message(message: Message) -> str:
        if not (msg_text := message.text):
            return ""

        if not msg_text.startswith("/"):
            return msg_text.strip()

        # It starts with a command
        parts = msg_text.split(" ", 1)
        if len(parts) > 1:
            return parts[1].strip()

        # Just the command, check if it's a reply
        if message.reply_to_message and message.reply_to_message.text:
            return message.reply_to_message.text

        return ""

    def __init__(
        self,
        id: str,
        from_chat_id: int,
        from_message_id: int,
        text: str,
        liked_by: list[int] | None = None,
        disliked_by: list[int] | None = None,
        user_id: int = 0,
    ):
        self.id = id
        self.from_chat_id = from_chat_id
        self.from_message_id = from_message_id
        self.text = text
        self.liked_by = liked_by or []
        self.disliked_by = disliked_by or []
        self.user_id = user_id

    @classmethod
    def from_update(cls, update: Update, text: str | None = None) -> "Proposal":
        if not (message := update.effective_message) or not (
            user := update.effective_user
        ):
            raise ValueError("Update has no effective message or user")

        proposal_id = str(message.chat.id + message.message_id)

        return cls(
            proposal_id,
            message.chat.id,
            message.message_id,
            text if text is not None else cls.proposal_text_from_message(message),
            user_id=user.id,
        )

    @classmethod
    def from_entity(cls, entity: datastore.Entity) -> "Proposal":
        return cls(
            entity.key.name,
            entity["from_chat_id"],
            entity["from_message_id"],
            entity["text"],
            liked_by=entity.get("liked_by", []),
            disliked_by=entity.get("disliked_by", []),
            user_id=entity.get("user_id", 0),
        )

    @classmethod
    def load(cls, id) -> Optional["Proposal"]:
        datastore_client = datastore.Client()
        key = datastore_client.key(cls.kind, id)

        entity = datastore_client.get(key)
        if entity is None:
            return entity

        return cls.from_entity(entity)

    @classmethod
    def load_all(cls) -> list["Proposal"]:
        datastore_client = datastore.Client()
        query = datastore_client.query(kind=cls.kind)
        return [cls.from_entity(entity) for entity in query.fetch()]

    def save(self):
        datastore_client = datastore.Client()
        key = datastore_client.key(self.kind, self.id)
        proposal_entity = datastore.Entity(key=key)

        proposal_entity["text"] = self.text
        proposal_entity["from_chat_id"] = self.from_chat_id
        proposal_entity["from_message_id"] = self.from_message_id
        proposal_entity["liked_by"] = self.liked_by
        proposal_entity["disliked_by"] = self.disliked_by
        proposal_entity["user_id"] = self.user_id

        datastore_client.put(proposal_entity)

    def delete(self) -> None:
        datastore_client = datastore.Client()
        key = datastore_client.key(self.kind, self.id)
        datastore_client.delete(key)

    def add_vote(self, positive, voter_id) -> None:
        if positive:
            add_set, remove_set = set(self.liked_by), set(self.disliked_by)
        else:
            add_set, remove_set = set(self.disliked_by), set(self.liked_by)

        if voter_id in remove_set:
            remove_set.remove(voter_id)

        add_set.add(voter_id)
        if positive:
            self.liked_by, self.disliked_by = list(add_set), list(remove_set)
        else:
            self.liked_by, self.disliked_by = list(remove_set), list(add_set)


class LongProposal(Proposal):
    kind = "LongProposal"
    phrase_class = LongPhrase


def get_proposal_class_by_kind(kind: str) -> type[Proposal]:
    if kind == LongProposal.kind:
        return LongProposal

    return Proposal
