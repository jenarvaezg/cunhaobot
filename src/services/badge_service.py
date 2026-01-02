import logging
from datetime import datetime, timedelta

from services.user_service import user_service
from infrastructure.datastore.usage import usage_repository


logger = logging.getLogger(__name__)


class Badge:
    def __init__(self, id: str, name: str, description: str, icon: str):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon


BADGES = [
    Badge("madrugador", "El del primer café", "Usar el bot antes de las 7:30 AM", "☕"),
    Badge(
        "trasnochador",
        "Cerrando el bar",
        "Usar el bot entre las 02:00 y las 05:00 AM",
        "🦉",
    ),
    Badge("fiera_total", "¡Qué pasa, fiera!", "Recibir o enviar 50 saludos", "🐯"),
    Badge("visionario", "Ojo de Halcón", "Usar el Cuñao Vision 10 veces", "👁️"),
    Badge(
        "pesao",
        "El de la esquina de la barra",
        "Usar el bot 10 veces en menos de 1 hora",
        "🍺",
    ),
    Badge("poeta", "Cervantes del Palillo", "Que te acepten 5 frases propuestas", "✍️"),
]


class BadgeService:
    def __init__(self, u_service=user_service, u_repo=usage_repository):
        self.user_service = u_service
        self.usage_repo = u_repo

    async def check_badges(self, user_id: str | int, platform: str) -> list[Badge]:
        """Checks and awards new badges to a user. Returns list of NEWLY awarded Badge objects."""
        user = self.user_service.get_user(user_id, platform)
        if not user:
            return []

        new_badge_ids = []
        current_badges = set(user.badges)
        now = datetime.now()

        # Update activity history
        if not hasattr(user, "last_usages") or user.last_usages is None:
            user.last_usages = []
        user.last_usages.append(now)
        # Keep only the last 20 usages to avoid entity size bloat
        user.last_usages = user.last_usages[-20:]

        # 1. Madrugador (05:00 - 07:30)
        if "madrugador" not in current_badges:
            if 5 <= now.hour < 7 or (now.hour == 7 and now.minute <= 30):
                new_badge_ids.append("madrugador")

        # 2. Trasnochador (02:00 - 05:00)
        if "trasnochador" not in current_badges:
            if 2 <= now.hour < 5:
                new_badge_ids.append("trasnochador")

        # 3. Fiera Total (50 saludos)
        if "fiera_total" not in current_badges:
            stats = usage_repository.get_user_usage_count(str(user_id), platform)
            if stats >= 50:
                new_badge_ids.append("fiera_total")

        # 4. Visionario (10 vision usages)
        if "visionario" not in current_badges:
            from models.usage import ActionType

            vision_count = self.usage_repo.get_user_action_count(
                str(user_id), platform, ActionType.VISION.value
            )
            if vision_count >= 10:
                new_badge_ids.append("visionario")

        # 5. Poeta (5 phrases proposed)
        if "poeta" not in current_badges:
            from infrastructure.datastore.phrase import phrase_repository

            user_phrases_count = phrase_repository.get_user_phrase_count(str(user_id))
            if user_phrases_count >= 5:
                new_badge_ids.append("poeta")

        # 6. Pesao (10 usages in 1 hour)
        if "pesao" not in current_badges:
            since = now - timedelta(hours=1)
            recent_count = len([u for u in user.last_usages if u >= since])
            if recent_count >= 10:
                new_badge_ids.append("pesao")

        # Always save user because last_usages has been updated
        if new_badge_ids:
            user.badges.extend(new_badge_ids)
            logger.info(f"User {user_id} awarded badges: {new_badge_ids}")

        self.user_service.save_user(user)

        new_badges = []
        for b_id in new_badge_ids:
            b_info = self.get_badge_info(b_id)
            if b_info:
                new_badges.append(b_info)

        return new_badges

    def get_badge_info(self, badge_id: str) -> Badge | None:
        return next((b for b in BADGES if b.id == badge_id), None)

    async def get_all_badges_progress(
        self, user_id: str | int, platform: str
    ) -> list[dict]:
        """Returns a list of all badges with current user progress."""
        from models.usage import ActionType

        user = self.user_service.get_user(user_id, platform)
        if not user:
            return []

        current_badges = set(user.badges)
        results = []

        # Get stats once
        total_usages = self.usage_repo.get_user_usage_count(str(user_id), platform)
        # We'll need vision count for Visionario
        vision_count = self.usage_repo.get_user_action_count(
            user_id, platform, ActionType.VISION.value
        )
        # We need approved phrases for Poeta
        from infrastructure.datastore.phrase import phrase_repository

        # Simple count of phrases authored by user that are in the main repo
        # (For now, let's assume phrases in repo are 'approved')
        user_phrases_count = phrase_repository.get_user_phrase_count(str(user_id))

        for badge in BADGES:
            is_earned = badge.id in current_badges
            progress = 100 if is_earned else 0
            current_val = 0
            target_val = 0

            if not is_earned:
                if badge.id == "fiera_total":
                    current_val = total_usages
                    target_val = 50
                    progress = min(100, int((current_val / target_val) * 100))
                elif badge.id == "visionario":
                    current_val = vision_count
                    target_val = 10
                    progress = min(100, int((current_val / target_val) * 100))
                elif badge.id == "poeta":
                    current_val = user_phrases_count
                    target_val = 5
                    progress = min(100, int((current_val / target_val) * 100))
                elif badge.id == "pesao":
                    since = datetime.now() - timedelta(hours=1)
                    if hasattr(user, "last_usages") and user.last_usages:
                        current_val = len([u for u in user.last_usages if u >= since])
                    else:
                        current_val = 0
                    target_val = 10
                    progress = min(100, int((current_val / target_val) * 100))
                # Time-based ones are binary for now
                elif badge.id in ["madrugador", "trasnochador"]:
                    current_val = 0
                    target_val = 1
                    progress = 0

            results.append(
                {
                    "badge": badge,
                    "is_earned": is_earned,
                    "progress": progress,
                    "current": current_val,
                    "target": target_val,
                }
            )

        return results


badge_service = BadgeService()
