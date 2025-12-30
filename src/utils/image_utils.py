import io
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

MAX_SIZE = (512, 512)
BORDER_SIZE = 3
SHADOW_COLOR = "black"


def _text_wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
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


def generate_png(text: str) -> BytesIO:
    font_path = "src/fonts/impact.ttf"
    font_size = 80
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
