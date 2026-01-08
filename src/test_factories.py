from polyfactory.factories.pydantic_factory import ModelFactory
from models.user import User
from models.chat import Chat
from models.phrase import Phrase
from models.proposal import Proposal, LongProposal


class UserFactory(ModelFactory[User]):
    __model__ = User


class ChatFactory(ModelFactory[Chat]):
    __model__ = Chat


class PhraseFactory(ModelFactory[Phrase]):
    __model__ = Phrase


class ProposalFactory(ModelFactory[Proposal]):
    __model__ = Proposal


class LongProposalFactory(ModelFactory[LongProposal]):
    __model__ = LongProposal
