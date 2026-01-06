import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, cast
from pydantic import BaseModel

from infrastructure.protocols import (
    UsageRepository,
    UserRepository,
    PhraseRepository,
    LongPhraseRepository,
    GiftRepository,
)

if TYPE_CHECKING:
    from models.user import User
    from services.user_service import UserService


logger = logging.getLogger(__name__)


class Badge(BaseModel):
    id: str
    name: str
    description: str
    icon: str


class BadgeProgress(BaseModel):
    badge: Badge
    is_earned: bool
    progress: int
    current: int
    target: int


BADGES = [
    Badge(
        id="novato",
        name="El nuevo del barrio",
        description="Primer uso del bot",
        icon="🐣",
    ),
    Badge(
        id="madrugador",
        name="El del primer café",
        description="Usar el bot antes de las 7:30 AM",
        icon="☕",
    ),
    Badge(
        id="trasnochador",
        name="Cerrando el bar",
        description="Usar el bot entre las 02:00 y las 05:00 AM",
        icon="🦉",
    ),
    Badge(
        id="fiera_total",
        name="¡Qué pasa, fiera!",
        description="Recibir o enviar 50 saludos",
        icon="🐯",
    ),
    Badge(
        id="visionario",
        name="Ojo de Halcón",
        description="Usar el Cuñao Vision 5 veces",
        icon="👁️",
    ),
    Badge(
        id="pesao",
        name="El de la esquina de la barra",
        description="Usar el bot 10 veces en menos de 1 hora",
        icon="🍺",
    ),
    Badge(
        id="poeta",
        name="Cervantes del Palillo",
        description="Que te acepten 5 frases propuestas",
        icon="✍️",
    ),
    Badge(
        id="autor",
        name="Catedrático de barra",
        description="Que te aprueben una frase",
        icon="🎓",
    ),
    Badge(
        id="incomprendido",
        name="Adelantado a su tiempo",
        description="Que te rechacen una frase",
        icon="🤐",
    ),
    Badge(
        id="charlatan",
        name="Pico de oro",
        description="Usar el modo IA 5 veces",
        icon="🗣️",
    ),
    Badge(
        id="melomano",
        name="Dando la nota",
        description="Usar el modo audio 5 veces",
        icon="🎶",
    ),
    Badge(
        id="insistente",
        name="Martillo pilón",
        description="Proponer 10 frases",
        icon="🔨",
    ),
    Badge(
        id="multiplataforma",
        name="Omnipresente",
        description="Vincular cuentas de distintas plataformas",
        icon="🌐",
    ),
    Badge(
        id="centro_atencion",
        name="El Centro de Atención",
        description="Que Paco te reaccione a un mensaje",
        icon="🌟",
    ),
    Badge(
        id="mecenas",
        name="El Mecenas",
        description="Generar 1 póster con IA",
        icon="🎨",
    ),
    Badge(
        id="coleccionista",
        name="El Coleccionista",
        description="Generar 5 pósters con IA",
        icon="🖼️",
    ),
    Badge(
        id="galerista",
        name="El Galerista",
        description="Generar 10 pósters con IA",
        icon="🏛️",
    ),
    Badge(
        id="vip",
        name="El Patrón",
        description="Pagar una suscripción Premium",
        icon="💎",
    ),
    Badge(
        id="rey_mago",
        name="El Rey Mago",
        description="Enviar un regalo digital",
        icon="🤴",
    ),
    Badge(
        id="consentido",
        name="El Consentido",
        description="Recibir un regalo digital",
        icon="🎁",
    ),
    Badge(
        id="viciado",
        name="Máquina Recreativa",
        description="Jugar 10 partidas al juego del palillo",
        icon="🕹️",
    ),
    Badge(
        id="parroquia",
        name="La Parroquia",
        description="Mantener una racha de 3 días jugando",
        icon="🍻",
    ),
    Badge(
        id="pinchito_oro",
        name="Pinchito de Oro",
        description="Conseguir más de 500 puntos en una partida",
        icon="🥇",
    ),
]


class BadgeService:
    def __init__(
        self,
        user_repo: UserRepository,
        usage_repo: UsageRepository,
        phrase_repo: PhraseRepository,
        long_phrase_repo: LongPhraseRepository,
        gift_repo: GiftRepository,
    ):
        self.user_repo = user_repo
        self.usage_repo = usage_repo
        self.phrase_repo = phrase_repo
        self.long_phrase_repo = long_phrase_repo
        self.gift_repo = gift_repo
        self._user_service: UserService | None = None

    @property
    def user_service(self) -> UserService:
        if self._user_service is None:
            # Lazy import to avoid circular dependency
            from services.user_service import UserService
            from infrastructure.datastore.proposal import (
                proposal_repository,
                long_proposal_repository,
            )
            from infrastructure.datastore.chat import chat_repository
            from infrastructure.datastore.link_request import link_request_repository
            from infrastructure.protocols import (
                UserRepository,
                ChatRepository,
                PhraseRepository,
                LongPhraseRepository,
                ProposalRepository,
                LongProposalRepository,
                LinkRequestRepository,
            )

            self._user_service = UserService(
                user_repo=cast(UserRepository, self.user_repo),
                chat_repo=cast(ChatRepository, chat_repository),
                phrase_repo=cast(PhraseRepository, self.phrase_repo),
                long_phrase_repo=cast(LongPhraseRepository, self.long_phrase_repo),
                proposal_repo=cast(ProposalRepository, proposal_repository),
                long_proposal_repo=cast(
                    LongProposalRepository, long_proposal_repository
                ),
                link_request_repo=cast(LinkRequestRepository, link_request_repository),
            )
        return self._user_service

    async def check_badges(
        self, user_id: str | int, platform: str, save: bool = True
    ) -> list[Badge]:
        """Checks and awards new badges to a user. Returns list of NEWLY awarded Badge objects."""
        from models.usage import ActionType

        user = await self.user_service.get_user(user_id, platform)
        if not user:
            return []

        new_badge_ids = []
        current_badges = set(user.badges)
        now = datetime.now(timezone.utc)

        # Update activity history
        if not hasattr(user, "last_usages") or user.last_usages is None:
            user.last_usages = []
        user.last_usages.append(now)
        user.last_usages = user.last_usages[-20:]

        # Novato
        if "novato" not in current_badges:
            new_badge_ids.append("novato")

        # Madrugador
        if "madrugador" not in current_badges:
            if 5 <= now.hour < 7 or (now.hour == 7 and now.minute <= 30):
                new_badge_ids.append("madrugador")

        # Trasnochador
        if "trasnochador" not in current_badges:
            if 2 <= now.hour < 5:
                new_badge_ids.append("trasnochador")

        # Fiera Total
        if "fiera_total" not in current_badges:
            stats = await self.usage_repo.get_user_usage_count(str(user_id))
            if stats >= 50:
                new_badge_ids.append("fiera_total")

        # Visionario
        if "visionario" not in current_badges:
            vision_count = await self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.VISION.value
            )
            if vision_count >= 5:
                new_badge_ids.append("visionario")

        # Poeta
        if "poeta" not in current_badges:
            # phrase_repo is now injected
            user_phrases_count = await self.phrase_repo.get_user_phrase_count(
                str(user_id)
            )
            if user_phrases_count >= 5:
                new_badge_ids.append("poeta")

        # Pesao
        if "pesao" not in current_badges:
            since = now - timedelta(hours=1)
            recent_count = len([u for u in user.last_usages if u >= since])
            if recent_count >= 10:
                new_badge_ids.append("pesao")

        # Autor
        if "autor" not in current_badges:
            approve_count = await self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.APPROVE.value
            )
            if approve_count >= 1:
                new_badge_ids.append("autor")

        # Incomprendido
        if "incomprendido" not in current_badges:
            reject_count = await self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.REJECT.value
            )
            if reject_count >= 1:
                new_badge_ids.append("incomprendido")

        # Charlatán
        if "charlatan" not in current_badges:
            ai_count = await self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.AI_ASK.value
            )
            if ai_count >= 5:
                new_badge_ids.append("charlatan")

        # Melómano
        if "melomano" not in current_badges:
            audio_count = await self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.AUDIO.value
            )
            if audio_count >= 5:
                new_badge_ids.append("melomano")

        # Insistente
        if "insistente" not in current_badges:
            propose_count = await self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.PROPOSE.value
            )
            if propose_count >= 10:
                new_badge_ids.append("insistente")

        # Multiplataforma
        if "multiplataforma" not in current_badges:
            raw_user = await self.user_repo.load_raw(user.id)
            if raw_user and raw_user.linked_to:
                new_badge_ids.append("multiplataforma")
            else:
                all_users = await self.user_repo.load_all(ignore_gdpr=True)
                if any(u.linked_to == user.id for u in all_users):
                    new_badge_ids.append("multiplataforma")

        # Centro de Atención
        if "centro_atencion" not in current_badges:
            reaction_count = await self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.REACTION_RECEIVED.value
            )
            if reaction_count >= 1:
                new_badge_ids.append("centro_atencion")

        # VIP
        if "vip" not in current_badges:
            sub_count = await self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.SUBSCRIPTION.value
            )
            if sub_count >= 1:
                new_badge_ids.append("vip")

        # El Rey Mago
        if "rey_mago" not in current_badges:
            gift_sent_count = await self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.GIFT_SENT.value
            )
            if gift_sent_count >= 1:
                new_badge_ids.append("rey_mago")

        # El Consentido
        if "consentido" not in current_badges:
            gift_received_count = await self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.GIFT_RECEIVED.value
            )
            if gift_received_count >= 1:
                new_badge_ids.append("consentido")

        # Poster badges
        if any(
            b not in current_badges for b in ["mecenas", "coleccionista", "galerista"]
        ):
            from infrastructure.datastore.poster_request import (
                poster_request_repository,
            )

            poster_count = await poster_request_repository.count_completed_by_user(
                user.id
            )
            if "mecenas" not in current_badges and poster_count >= 1:
                new_badge_ids.append("mecenas")
            if "coleccionista" not in current_badges and poster_count >= 5:
                new_badge_ids.append("coleccionista")
            if "galerista" not in current_badges and poster_count >= 10:
                new_badge_ids.append("galerista")

        # Game badges
        if "viciado" not in current_badges and user.game_stats >= 10:
            new_badge_ids.append("viciado")

        if "parroquia" not in current_badges and user.game_streak >= 3:
            new_badge_ids.append("parroquia")

        if "pinchito_oro" not in current_badges and user.game_high_score >= 500:
            new_badge_ids.append("pinchito_oro")

        if new_badge_ids:
            user.badges.extend(new_badge_ids)
            logger.info(f"User {user_id} awarded badges: {new_badge_ids}")

        if save:
            await self.user_service.save_user(user)

        new_badges = []
        for b_id in new_badge_ids:
            b_info = self.get_badge_info(b_id)
            if b_info:
                new_badges.append(b_info)

        return new_badges

    def get_badge_info(self, badge_id: str) -> Badge | None:
        return next((b for b in BADGES if b.id == badge_id), None)

    async def get_all_badges_progress(
        self,
        user_id: str | int,
        platform: str,
        user: User | None = None,
    ) -> list[BadgeProgress]:
        """Returns a list of all badges with current user progress."""
        from models.usage import ActionType

        if not user:
            user = await self.user_service.get_user(user_id, platform)

        if not user:
            return []

        current_badges = set(user.badges)
        results: list[BadgeProgress] = []

        from infrastructure.datastore.poster_request import poster_request_repository

        # Get stats in parallel
        (
            total_usages,
            vision_count,
            ai_count,
            audio_count,
            propose_count,
            approve_count,
            reject_count,
            reaction_count,
            sub_count,
            gift_sent_count,
            gift_received_count,
            user_phrases_count,
            poster_count,
        ) = await asyncio.gather(
            self.usage_repo.get_user_usage_count(str(user_id)),
            self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.VISION.value
            ),
            self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.AI_ASK.value
            ),
            self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.AUDIO.value
            ),
            self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.PROPOSE.value
            ),
            self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.APPROVE.value
            ),
            self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.REJECT.value
            ),
            self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.REACTION_RECEIVED.value
            ),
            self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.SUBSCRIPTION.value
            ),
            self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.GIFT_SENT.value
            ),
            self.usage_repo.get_user_action_count(
                str(user_id), action=ActionType.GIFT_RECEIVED.value
            ),
            self.phrase_repo.get_user_phrase_count(str(user_id)),
            poster_request_repository.count_completed_by_user(user_id),
        )

        for badge in BADGES:
            is_earned = badge.id in current_badges
            progress = 100 if is_earned else 0
            current_val = 0
            target_val = 0

            if not is_earned:
                if badge.id == "fiera_total":
                    current_val = total_usages
                    target_val = 50
                elif badge.id == "visionario":
                    current_val = vision_count
                    target_val = 5
                elif badge.id == "poeta":
                    current_val = user_phrases_count
                    target_val = 5
                elif badge.id == "charlatan":
                    current_val = ai_count
                    target_val = 5
                elif badge.id == "melomano":
                    current_val = audio_count
                    target_val = 5
                elif badge.id == "insistente":
                    current_val = propose_count
                    target_val = 10
                elif badge.id == "autor":
                    current_val = approve_count
                    target_val = 1
                elif badge.id == "incomprendido":
                    current_val = reject_count
                    target_val = 1
                elif badge.id == "pesao":
                    since = datetime.now(timezone.utc) - timedelta(hours=1)
                    if hasattr(user, "last_usages") and user.last_usages:
                        current_val = len([u for u in user.last_usages if u >= since])
                    else:
                        current_val = 0
                    target_val = 10
                elif badge.id == "novato":
                    current_val = 1 if total_usages > 0 else 0
                    target_val = 1
                elif badge.id == "centro_atencion":
                    current_val = reaction_count
                    target_val = 1
                elif badge.id == "vip":
                    current_val = sub_count
                    target_val = 1
                elif badge.id == "rey_mago":
                    current_val = gift_sent_count
                    target_val = 1
                elif badge.id == "consentido":
                    current_val = gift_received_count
                    target_val = 1
                elif badge.id == "mecenas":
                    current_val = poster_count
                    target_val = 1
                elif badge.id == "coleccionista":
                    current_val = poster_count
                    target_val = 5
                elif badge.id == "galerista":
                    current_val = poster_count
                    target_val = 10
                elif badge.id == "viciado":
                    current_val = user.game_stats
                    target_val = 10
                elif badge.id == "parroquia":
                    current_val = user.game_streak
                    target_val = 3
                elif badge.id == "pinchito_oro":
                    current_val = user.game_high_score
                    target_val = 500

                if target_val > 0:
                    progress = min(100, int((current_val / target_val) * 100))

            results.append(
                BadgeProgress(
                    badge=badge,
                    is_earned=is_earned,
                    progress=progress,
                    current=current_val,
                    target=target_val,
                )
            )

        return results
