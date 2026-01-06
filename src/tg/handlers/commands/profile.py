import html
import logging
from telegram import Update, constants
from telegram.ext import CallbackContext
from tg.decorators import log_update
from core.container import services
from models.usage import ActionType
from tg.utils.badges import notify_new_badges
from core.config import config

logger = logging.getLogger(__name__)


@log_update
async def handle_profile(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message) or not message.from_user:
        return

    user_id = message.from_user.id
    platform = "telegram"

    # Ensure ID is handled as string for consistent lookup
    user = await services.user_service.get_user(str(user_id), platform)
    if not user:
        # Try numeric lookup as fallback just in case
        user = await services.user_service.get_user(user_id, platform)

    if not user:
        p = (await services.phrase_service.get_random(long=False)).text
        await message.reply_text(
            f"Todavía no tengo tu ficha, {p}. ¡Empieza a usar el bot!"
        )
        return

    try:
        # Log usage
        new_badges = await services.usage_service.log_usage(
            user_id=user_id,
            platform="telegram",
            action=ActionType.COMMAND,
            metadata={"command": "profile"},
        )
        await notify_new_badges(update, context, new_badges)

        stats = await services.usage_service.get_user_stats(user_id, platform)
        all_badges_progress = await services.badge_service.get_all_badges_progress(
            user_id, platform
        )

        earned_list: list[str] = []

        for p in all_badges_progress:
            badge = p.badge
            if p.is_earned:
                earned_list.append(
                    f"{badge.icon} <b>{html.escape(badge.name)}</b>\n"
                    f"<i>{html.escape(badge.description)}</i>"
                )

        badges_text = ""
        if earned_list:
            badges_text = "\n" + "\n".join(earned_list)
        else:
            badges_text = "\n<i>Todavía no tienes medallas, ¡dale caña!</i>"

        user_name = html.escape(user.name or "Desconocido")
        profile_url = f"{config.base_url}/user/{user.id}/profile"
        text = (
            f"🔗 <a href='{profile_url}'>Ver perfil en la web</a>\n\n"
            f"👤 <b>Perfil de {user_name}</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🏆 <b>Puntos:</b> {user.points}\n"
            f"📊 <b>Usos totales:</b> {stats['total_usages']}\n"
            f"🎖️ <b>Logros conseguidos:</b> {badges_text}"
        )

        await message.reply_text(text, parse_mode=constants.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error in handle_profile: {e}")
        import traceback

        logger.error(traceback.format_exc())
        # Fallback to simple text if HTML fails
        user_name = user.name or "máquina"
        await message.reply_text(
            f"Error al cargar el perfil ({type(e).__name__}: {e}), {user_name}. Inténtalo de nuevo."
        )
