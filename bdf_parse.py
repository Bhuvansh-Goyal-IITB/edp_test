from PIL import Image
import math
from enum import Enum, auto


class Text_Justification(Enum):
    FULL = auto()
    LEFT = auto()


class Line_Break_Algorithm(Enum):
    GREEDY = auto()
    OPTIMAL = auto()


class Glyph:
    def __init__(
        self,
        code_point: int,
        x_advance: int,
        bbox: tuple[int, int, int, int],
        bitmap: bytes,
    ) -> None:
        self.code_point = code_point
        self.x_advance = x_advance
        self.bbox = bbox
        self.bitmap = bitmap


class BDF_Font:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.glyphs: list[Glyph] = []

        self.ascent: int = 0
        self.descent: int = 0
        self.pixel_size: int = 0

        self.parse_file()

    def parse_file(self) -> None:
        with open(self.file_path, "r", encoding="utf-8") as fp:
            lines = fp.readlines()
            i = 0
            while i < len(lines):
                if "PIXEL_SIZE" in lines[i]:
                    self.pixel_size = int(lines[i].split(" ")[1])
                    i += 1
                elif "FONT_ASCENT" in lines[i]:
                    self.ascent = int(lines[i].split(" ")[1])
                    i += 1
                elif "FONT_DESCENT" in lines[i]:
                    self.descent = int(lines[i].split(" ")[1])
                    i += 1
                elif "STARTCHAR" in lines[i]:
                    i += 1
                    code_point = int(lines[i].split(" ")[1])

                    i += 2
                    x_advance = int(lines[i].split(" ")[1])

                    i += 1
                    bbox = (
                        int(lines[i].split(" ")[1]),
                        int(lines[i].split(" ")[2]),
                        int(lines[i].split(" ")[3]),
                        int(lines[i].split(" ")[4]),
                    )

                    i += 2
                    bitmap_text = ""

                    while "ENDCHAR" not in lines[i]:
                        bitmap_text += lines[i]
                        i += 1

                    bitmap = bytes.fromhex(bitmap_text)

                    self.glyphs.append(Glyph(code_point, x_advance, bbox, bitmap))
                else:
                    i += 1

    def optimal_line_indices(self, text_block, page_width):
        line_indices = []

        words = []
        word_indices = []

        word_buffer = ""
        word_start_index = 0

        for i, char in enumerate(text_block):
            if char != " " and i != len(text_block) - 1:
                if len(word_buffer) == 0:
                    word_start_index = i
                word_buffer += char
            else:
                if i == len(text_block) - 1:
                    if len(word_buffer) == 0:
                        word_start_index = i
                    word_buffer += char

                if len(word_buffer) > 0:
                    words.append(word_buffer)
                    if i == len(text_block) - 1:
                        word_indices.append((word_start_index, i))
                    else:
                        word_indices.append((word_start_index, i - 1))

                word_buffer = ""

        word_widths = [self.get_width(word) for word in words]
        word_widths.append(0)
        space_width = self.get_width(" ")

        dp = [float("inf") for _ in range(len(words) + 1)]
        next_break = [0 for _ in range(len(words))]

        dp[len(words)] = 0

        for i in range(len(words) - 1, -1, -1):
            width = word_widths[i]

            for j in range(i + 1, len(words) + 1):
                cost = 0
                line_width = width + ((j - i - 1) * space_width)
                if line_width > page_width:
                    cost = float("inf")
                else:
                    cost = (page_width - line_width) ** 3

                cost += dp[j]

                width += word_widths[j]

                if cost < dp[i]:
                    dp[i] = cost
                    next_break[i] = j

        word_index = 0
        while True:
            if word_index == len(words):
                break

            line_indices.append(
                (
                    word_indices[word_index][0],
                    word_indices[next_break[word_index] - 1][1],
                )
            )

            word_index = next_break[word_index]

        return line_indices

    def greedy_line_indices(self, text_block, page_width):
        line_indices = [tuple([0])]

        x = 0

        word_buffer = ""

        word_start_index = 0
        prev_word_end_index = 0

        for i, char in enumerate(text_block):
            if char != " " and i != len(text_block) - 1:
                if len(word_buffer) == 0:
                    word_start_index = i
                word_buffer += char
            else:
                if i == len(text_block) - 1:
                    if len(word_buffer) == 0:
                        word_start_index = i
                    word_buffer += char

                if len(word_buffer) > 0:
                    word_width = self.get_width(word_buffer)

                    if x + word_width >= page_width:
                        x = word_width
                        prev_index_start = line_indices[-1][0]
                        line_indices.pop()
                        line_indices.append((prev_index_start, prev_word_end_index))
                        line_indices.append(tuple([word_start_index]))
                    else:
                        x += word_width

                    prev_word_end_index = i - 1

                    if char == " ":
                        x += self.get_width(" ")
                word_buffer = ""

        prev_index_start = line_indices[-1][0]
        line_indices.pop()
        line_indices.append((prev_index_start, len(text_block) - 1))

        return line_indices

    def render_line_indices(
        self,
        line_indices,
        img: Image.Image,
        text: str,
        margin: tuple[int, int] = (0, 0),
        text_justification: Text_Justification = Text_Justification.FULL,
    ):
        x, y = margin[0], margin[1] + self.ascent - 1

        for line_index in line_indices:
            words = []
            word_buffer = ""

            line = text[line_index[0] : line_index[1] + 1]
            for i, char in enumerate(line):
                if char != " ":
                    word_buffer += char
                    if i == len(line) - 1:
                        words.append(word_buffer)
                else:
                    words.append(word_buffer)
                    word_buffer = ""

            width = 0
            for word in words:
                width += self.get_width(word)

            gap_sizes = []

            if len(words) > 1 and text_justification == Text_Justification.FULL:
                gap_sizes = [
                    (img.size[0] - (2 * margin[0]) - width) // (len(words) - 1)
                    for _ in range(len(words))
                ]

                gap_sizes_sum = sum(gap_sizes)

                remaining = img.size[0] - (2 * margin[0]) - width - gap_sizes_sum

                add_at_front = True
                for i in range(remaining):
                    if add_at_front:
                        gap_sizes[i] += 1
                    else:
                        gap_sizes[len(gap_sizes) - i - 1] += 1

                    add_at_front = not add_at_front

                if width < 0.6 * (img.size[0] - (2 * margin[0])):
                    gap_sizes = []

            for i, word in enumerate(words):
                for char in word:
                    if char == "\n" or char == "\r":
                        continue

                    glyph = self.get_glyph(ord(char))

                    if glyph is not None:
                        self.render_glyph(img, (x, y), glyph)
                        x += glyph.x_advance

                if len(gap_sizes) > 0 and text_justification == Text_Justification.FULL:
                    x += gap_sizes[i]
                else:
                    x += self.get_width(" ")

            y += self.ascent + self.descent - 1
            x = margin[0]

            if y + self.descent + margin[1] >= img.height:
                break

    # The text should not contain \n or \f
    def render_text_block(
        self,
        img: Image.Image,
        text: str,
        margin: tuple[int, int] = (0, 0),
        line_break_algorithm: Line_Break_Algorithm = Line_Break_Algorithm.GREEDY,
        text_justification: Text_Justification = Text_Justification.FULL,
    ):
        line_indices = []
        if line_break_algorithm == Line_Break_Algorithm.GREEDY:
            line_indices = self.greedy_line_indices(text, img.size[0] - (2 * margin[0]))
        else:
            line_indices = self.optimal_line_indices(
                text, img.size[0] - (2 * margin[0])
            )

        x, y = margin[0], margin[1] + self.ascent - 1

        for line_index in line_indices:
            words = []
            word_buffer = ""

            line = text[line_index[0] : line_index[1] + 1]
            for i, char in enumerate(line):
                if char != " ":
                    word_buffer += char
                    if i == len(line) - 1:
                        words.append(word_buffer)
                else:
                    words.append(word_buffer)
                    word_buffer = ""

            width = 0
            for word in words:
                width += self.get_width(word)

            gap_sizes = []

            if len(words) > 1 and text_justification == Text_Justification.FULL:
                gap_sizes = [
                    (img.size[0] - (2 * margin[0]) - width) // (len(words) - 1)
                    for _ in range(len(words))
                ]

                gap_sizes_sum = sum(gap_sizes)

                remaining = img.size[0] - (2 * margin[0]) - width - gap_sizes_sum

                add_at_front = True
                for i in range(remaining):
                    if add_at_front:
                        gap_sizes[i] += 1
                    else:
                        gap_sizes[len(gap_sizes) - i - 1] += 1

                    add_at_front = not add_at_front

                if width < 0.6 * (img.size[0] - (2 * margin[0])):
                    gap_sizes = []

            for i, word in enumerate(words):
                for char in word:
                    glyph = self.get_glyph(ord(char))

                    if glyph is not None:
                        self.render_glyph(img, (x, y), glyph)
                        x += glyph.x_advance

                if len(gap_sizes) > 0 and text_justification == Text_Justification.FULL:
                    x += gap_sizes[i]
                else:
                    x += self.get_width(" ")

            y += self.ascent + self.descent - 1
            x = margin[0]

            if y + self.descent + margin[1] >= img.height:
                break

    def render_text(
        self,
        img: Image.Image,
        text: str,
        margin: tuple[int, int] = (0, 0),
    ):
        img_width, img_height = img.size

        x, y = margin[0], margin[1] + self.ascent - 1

        for line in text.split("\n"):
            for word in line.split(" "):
                width = self.get_width(word)

                if x + width + margin[0] >= img_width:
                    x = margin[0]
                    y += self.ascent + self.descent - 1

                if y + self.descent + margin[1] >= img_height:
                    break

                for char in word:
                    code_point = ord(char)
                    glyph = self.get_glyph(code_point)

                    if glyph is None:
                        continue

                    self.render_glyph(img, (x, y), glyph)
                    x += glyph.x_advance

                glyph = self.get_glyph(32)
                if (glyph is not None) and not (
                    x + glyph.x_advance + margin[0] >= img_width
                ):
                    self.render_glyph(img, (x, y), glyph)
                    x += glyph.x_advance

            x = margin[0]
            y += self.ascent + self.descent - 1

            if y + self.descent + margin[1] >= img_height:
                break

    def render_glyph(
        self, img: Image.Image, baseline_origin: tuple[int, int], glyph: Glyph
    ):
        for bmp_y in range(0, glyph.bbox[1]):
            for bmp_x in range(0, glyph.bbox[0]):
                x = bmp_x + baseline_origin[0] + glyph.bbox[2]
                y = bmp_y + baseline_origin[1] - glyph.bbox[1] - glyph.bbox[3] + 1

                if x >= img.width or y >= img.height:
                    continue

                if glyph.bitmap[bmp_x // 8 + (bmp_y * math.ceil(glyph.bbox[0] / 8))] & (
                    1 << (7 - (bmp_x % 8))
                ):
                    img.putpixel((x, y), 0)

    def render_code_point(
        self, img: Image.Image, baseline_origin: tuple[int, int], code_point: int
    ):
        glyph = self.get_glyph(code_point)

        if glyph is not None:
            self.render_glyph(img, baseline_origin, glyph)

    def get_width(self, string):
        width = 0
        for char in string:
            glyph = self.get_glyph(ord(char))

            if glyph is not None:
                width += glyph.x_advance

        return width

    def get_glyph_array(self) -> list[Glyph]:
        return self.glyphs

    def get_glyph(self, code_point) -> Glyph | None:
        s = 0
        e = len(self.glyphs) - 1

        m = (s + e) // 2

        while s < e:
            if self.glyphs[m].code_point > code_point:
                e = m - 1
            elif self.glyphs[m].code_point < code_point:
                s = m + 1
            else:
                return self.glyphs[m]

            m = (s + e) // 2

        if self.glyphs[m].code_point == code_point:
            return self.glyphs[m]
        else:
            return None


if __name__ == "__main__":
    from html_parse import extract_epub_text

    TEXT = extract_epub_text("./catcher_in_the_rye.epub")
    TEXT = TEXT.split("\f")[2]
    TEXT = TEXT.split("\n")[1]

    img_size = (480, 648)
    margin = (20, 20)

    font = BDF_Font("font.bdf")
    img = Image.new("1", img_size, 1)

    text_justification = Text_Justification.LEFT

    font.render_text_block(
        img, TEXT, margin, Line_Break_Algorithm.OPTIMAL, text_justification
    )

    img.save("optimal.png")
