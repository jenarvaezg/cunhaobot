from telegram import Update


def user_from_update(update: Update) -> str:
    user = update.effective_user
    if user is None:
        # channel post, ignore
        return ''

    first_name = user.first_name or ''
    last_name = user.last_name or ''
    username = user.username or ''

    to_ret = f"{first_name} {last_name}".rstrip()

    if username:
        to_ret += f" con nombre de usuario @{username}"

    return to_ret
