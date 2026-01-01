import logging
from datetime import datetime

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
    Badge("poeta", "Cervantes del Palillo", "Que te ayuden 5 frases propuestas", "✍️"),
]


class BadgeService:
    def __init__(self, u_service=user_service, u_repo=usage_repository):
        self.user_service = u_service
        self.usage_repo = u_repo

    async def check_badges(self, user_id: str | int, platform: str) -> list[str]:
        """Checks and awards new badges to a user. Returns list of NEWLY awarded badge IDs."""
        user = self.user_service.get_user(user_id, platform)
        if not user:
            return []

        new_badges = []
        current_badges = set(user.badges)
        now = datetime.now()

        # 1. Madrugador (05:00 - 07:30)
        if "madrugador" not in current_badges:
            if 5 <= now.hour < 7 or (now.hour == 7 and now.minute <= 30):
                new_badges.append("madrugador")

        # 2. Trasnochador (02:00 - 05:00)
        if "trasnochador" not in current_badges:
            if 2 <= now.hour < 5:
                new_badges.append("trasnochador")

        # 3. Fiera Total (50 saludos)
        if "fiera_total" not in current_badges:
            # We can use the usage repo to count ActionType.SALUDO
            # For now, let's keep it simple and check if this user has enough total usages
            # or we could query the usage repo properly.
            # Let's do a simple count for now.
            if user.usages >= 50:  # Simplification for first version
                new_badges.append("fiera_total")

        if new_badges:
            user.badges.extend(new_badges)
            self.user_service.save_user(user)
            logger.info(f"User {user_id} awarded badges: {new_badges}")

        return new_badges

    def get_badge_info(self, badge_id: str) -> Badge | None:
        return next((b for b in BADGES if b.id == badge_id), None)


badge_service = BadgeService()
