import html
import logging
from telegram import Update, constants
from telegram.ext import CallbackContext
from tg.decorators import log_update
from services import user_service, usage_service, badge_service, phrase_service
from models.usage import ActionType

logger = logging.getLogger(__name__)


@log_update
async def handle_profile(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message) or not message.from_user:
        return

    user_id = message.from_user.id
    platform = "telegram"

    # Ensure ID is handled as string for consistent lookup
    user = user_service.get_user(str(user_id), platform)
    if not user:
        # Try numeric lookup as fallback just in case
        user = user_service.get_user(user_id, platform)

    if not user:
        p = phrase_service.get_random(long=False).text
        await message.reply_text(
            f"Todavía no tengo tu ficha, {p}. ¡Empieza a usar el bot!"
        )
        return

    try:
        # Log usage
        await usage_service.log_usage(
            user_id=user_id,
            platform=platform,
            action=ActionType.COMMAND,
            metadata={"command": "profile"},
        )

        stats = usage_service.get_user_stats(user_id, platform)

        badges_text = ""
        if user.badges:
            badge_infos = []
            for b_id in user.badges:
                b_info = badge_service.get_badge_info(b_id)
                if b_info:
                    badge_infos.append(
                        f"{b_info.icon} <b>{html.escape(b_info.name)}</b>"
                    )
            badges_text = "\n" + "\n".join(badge_infos)
        else:
            badges_text = "\n<i>Todavía no tienes medallas, ¡dale caña!</i>"

        user_name = html.escape(user.name or "Desconocido")
        text = (
            f"👤 <b>Perfil de {user_name}</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🏆 <b>Puntos:</b> {user.points}\n"
            f"📊 <b>Usos totales:</b> {stats['total_usages']}\n"
            f"🎖️ <b>Logros:</b> {badges_text}"
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
