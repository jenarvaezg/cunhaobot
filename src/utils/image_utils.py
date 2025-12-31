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
    bbox = font.getbbox(text)
    if (bbox[2] - bbox[0]) <= max_width:
        lines.append(text)
    else:
        # split the line by spaces to get words
        words = text.split(" ")
        i = 0
        # append every word to a line while its width is shorter than image width
        while i < len(words):
            line = ""
            while i < len(words):
                next_word = words[i]
                test_line = line + next_word + " "
                test_bbox = font.getbbox(test_line.strip())
                if (test_bbox[2] - test_bbox[0]) <= max_width:
                    line = test_line
                    i += 1
                else:
                    break
            if not line:
                line = words[i]
                i += 1
            # when the line gets longer than the max width do not append the word,
            # add the line to the lines array
            lines.append(line.strip())
    return lines


def generate_png(text: str) -> BytesIO:
    font_path = "src/fonts/impact.ttf"
    font = None
    lines = []
    line_height = 0

    # Increase horizontal safety margin for the wrap
    wrap_width = MAX_SIZE[0] - (BORDER_SIZE * 2) - 20

    for font_size in range(80, 1, -1):
        font = ImageFont.truetype(font_path, size=font_size)
        lines = _text_wrap(text, font, wrap_width)

        ascent, descent = font.getmetrics()
        # Small gap between lines (5% of ascent)
        gap = int(ascent * 0.05)
        line_height = ascent + descent + gap

        # Total height: All lines including gaps, minus the last gap, plus borders
        text_block_height = (len(lines) * line_height) - gap
        sum_y = text_block_height + (BORDER_SIZE * 2)

        longest_x = 0
        for line in lines:
            bbox = font.getbbox(line)
            width = bbox[2] - bbox[0]
            # Account for the stroke width in the width check
            longest_x = max(longest_x, width + BORDER_SIZE * 2 + 10)

        if sum_y <= MAX_SIZE[1] and longest_x <= MAX_SIZE[0]:
            break

    if font is None:
        raise ValueError("Could not calculate font size")

    image_size = (MAX_SIZE[0], int(sum_y))
    img = Image.new("RGBA", image_size)
    img_draw = ImageDraw.Draw(img)

    # Use BORDER_SIZE as the symmetric margin for top and bottom
    current_y = BORDER_SIZE
    for line in lines:
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        line_x = (image_size[0] - line_width) // 2

        # Use native stroke_width for a much cleaner and more reliable border
        img_draw.text(
            (line_x, current_y),
            line,
            font=font,
            fill="white",
            stroke_width=BORDER_SIZE,
            stroke_fill=SHADOW_COLOR,
            anchor="lt",
        )
        current_y += line_height

    b = io.BytesIO()
    img.save(b, "PNG")
    b.seek(0)
    return b
