import io
import os
from typing import BinaryIO

import telegram
from PIL import Image, ImageDraw, ImageFont

MAX_SIZE = (512, 512)
BORDER_SIZE = 3
SHADOW_COLOR = "black"
STICKER_EMOJIS = "😎"

owner_id = int(os.environ["OWNER_ID"])
curators_chat_id = int(os.environ.get("MOD_CHAT_ID", "-1"))


def _text_wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int):
    lines = []
    # If the width of the text is smaller than image width
    # we don't need to split it, just add it to the lines array
    # and return
    if font.getbbox(text)[2] <= max_width:
        lines.append(text)
    else:
        # split the line by spaces to get words
        words = text.split(" ")
        i = 0
        # append every word to a line while its width is shorter than image width
        while i < len(words):
            line = ""
            while i < len(words) and font.getbbox(line + words[i])[2] <= max_width:
                line = line + words[i] + " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            # when the line gets longer than the max width do not append the word,
            # add the line to the lines array
            lines.append(line)
    return lines


def _draw_text_with_border(
    text: str,
    text_position: tuple[int, int],
    font: ImageFont.FreeTypeFont,
    draw: ImageDraw.ImageDraw,
) -> None:
    x, y = text_position
    # draw border
    draw.text((x - BORDER_SIZE, y - BORDER_SIZE), text, font=font, fill=SHADOW_COLOR)
    draw.text((x + BORDER_SIZE, y - BORDER_SIZE), text, font=font, fill=SHADOW_COLOR)
    draw.text((x - BORDER_SIZE, y + BORDER_SIZE), text, font=font, fill=SHADOW_COLOR)
    draw.text((x + BORDER_SIZE, y + BORDER_SIZE), text, font=font, fill=SHADOW_COLOR)

    # now draw the text over it
    draw.text((x, y), text, font=font)


def generate_png(text: str) -> BinaryIO:
    font_path = "fonts/impact.ttf"
    sum_y = 0
    font = None
    lines = []

    for font_size in range(80, 1, -1):
        font = ImageFont.truetype(font_path, size=font_size)
        lines = _text_wrap(text, font, MAX_SIZE[0] - BORDER_SIZE * 2)
        sum_y = sum(
            (font.getbbox(line)[3] - font.getbbox(line)[1]) + BORDER_SIZE * 2
            for line in lines
        )
        longest_x = max(font.getbbox(line)[2] + BORDER_SIZE * 2 for line in lines)
        if sum_y < MAX_SIZE[1] and longest_x < MAX_SIZE[0]:
            break

    if font is None:
        raise ValueError("Could not calculate font size")

    image_size = (MAX_SIZE[0], int(sum_y))
    img = Image.new("RGBA", image_size)
    img_draw = ImageDraw.Draw(img)

    bbox_hg = font.getbbox("hg")
    line_height = bbox_hg[3] - bbox_hg[1]
    y = BORDER_SIZE
    for line in lines:
        line_x = int((image_size[0] - font.getbbox(line)[2] + BORDER_SIZE * 2) / 2)

        _draw_text_with_border(line, (line_x, y), font, img_draw)
        y = y + line_height

    b = io.BytesIO()
    img.save(b, "PNG")
    b.seek(0)
    return b


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

    stickerset_now = await bot.get_sticker_set(stickerset_name)
    stickers_now = {s.file_id for s in stickerset_now.stickers}

    return (stickers_now - stickers_before).pop()


async def delete_sticker(bot: telegram.Bot, sticker_file_id: str) -> None:
    await bot.delete_sticker_from_set(sticker_file_id)
