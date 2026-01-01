import logging
import asyncio
from datetime import datetime
from services import user_service, phrase_service, badge_service, usage_service
from models.usage import ActionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def backfill():
    logger.info("Iniciando proceso de recuperación de datos... ¡A ver qué nos encontramos!")
    
    # 1. Cargar todos los usuarios
    users = user_service.user_repo.load_all(ignore_gdpr=True)
    logger.info(f"Procesando {len(users)} usuarios...")

    # 2. Cargar todas las frases para contar autoría
    all_phrases = phrase_service.phrase_repo.load_all()
    all_long_phrases = phrase_service.long_repo.load_all()
    
    # Mapear cuántas frases ha propuesto cada uno
    authorship = {}
    for p in all_phrases + all_long_phrases:
        if p.user_id:
            uid = str(p.user_id)
            authorship[uid] = authorship.get(uid, 0) + 1

    for user in users:
        user_id = str(user.id)
        logger.info(f"Analizando a: {user.name} ({user_id})")
        
        new_badges = []
        current_badges = set(user.badges or [])

        # --- LOGRO: Fiera Total (Usos) ---
        if "fiera_total" not in current_badges and user.usages >= 50:
            logger.info(f"  - ¡Vaya fiera! Le toca medalla por sus {user.usages} usos.")
            new_badges.append("fiera_total")

        # --- LOGRO: Poeta (Frases aprobadas) ---
        count = authorship.get(user_id, 0)
        if "poeta" not in current_badges and count >= 5:
            logger.info(f"  - ¡Menudo Cervantes! Tiene {count} frases aprobadas.")
            new_badges.append("poeta")

        # Actualizar si hay novedades
        if new_badges:
            user.badges = list(current_badges.union(new_badges))
            user_service.save_user(user)
            logger.info(f"  - Medallas actualizadas: {new_badges}")

        # --- RECONSTRUCCIÓN DE USOS (Opcional/Simbólico) ---
        # Como no tenemos timestamps del pasado, creamos un registro "Legacy" 
        # para que el nuevo sistema de analíticas no empiece de cero.
        # Solo lo hacemos si el usuario tiene usos pero no hay registros de UsageRecord.
        usage_count = usage_service.repo.get_user_usage_count(user_id, user.platform)
        if usage_count == 0 and user.usages > 0:
            logger.info(f"  - Migrando {user.usages} usos antiguos a la nueva tabla.")
            # Creamos un registro especial por el total (podríamos crear N registros, pero para no saturar...)
            # Vamos a crear al menos uno para que el count() detecte la actividad
            await usage_service.log_usage(
                user_id=user_id,
                platform=user.platform,
                action=ActionType.PHRASE,
                metadata={"note": "Carga inicial desde sistema antiguo", "legacy_count": user.usages}
            )

    logger.info("¡Proceso terminado, máquina! Ya tenemos el bar al día.")

if __name__ == "__main__":
    asyncio.run(backfill())
