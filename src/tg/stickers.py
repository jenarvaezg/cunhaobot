import os
from typing import BinaryIO

import telegram

STICKER_EMOJIS = "😎"

owner_id = int(os.environ["OWNER_ID"])
curators_chat_id = int(os.environ.get("MOD_CHAT_ID", "-1"))


async def upload_sticker(
    bot: telegram.Bot,
    sticker_png: BinaryIO,
    stickerset_template: str,
    stickerset_title_template: str,
) -> str:
    from telegram import InputSticker

    file_id = (
        await bot.upload_sticker_file(owner_id, sticker_png, sticker_format="static")
    ).file_id
    offset = 0
    stickers_before = set()
    while True:
        offset += 1
        stickerset_name = stickerset_template.format(offset)
        try:
            stickerset = await bot.get_sticker_set(stickerset_name)
            stickers_before = {s.file_id for s in stickerset.stickers}
            await bot.add_sticker_to_set(
                owner_id,
                stickerset_name,
                sticker=InputSticker(file_id, [STICKER_EMOJIS], format="static"),
            )
            break
        except telegram.error.BadRequest as e:
            if e.message in ["Stickerpack_stickers_too_much", "Stickers_too_much"]:
                continue  # Try to find next stickerset, maybe it has room for you :)
            elif e.message == "Stickerset_invalid":
                # No stickerset, create it!
                stickerset_title = stickerset_title_template.format(offset)
                await bot.create_new_sticker_set(
                    owner_id,
                    stickerset_name,
                    stickerset_title,
                    stickers=[InputSticker(file_id, [STICKER_EMOJIS], format="static")],
                    sticker_type="regular",
                )
                break

    stickerset_now = await bot.get_sticker_set(stickerset_name)
    stickers_now = {s.file_id for s in stickerset_now.stickers}

    return (stickers_now - stickers_before).pop()


async def delete_sticker(bot: telegram.Bot, sticker_file_id: str) -> None:
    await bot.delete_sticker_from_set(sticker_file_id)
