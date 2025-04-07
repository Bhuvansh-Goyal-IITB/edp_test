from PIL import Image
import math
from pathlib import Path


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
        with open(self.file_path, "r") as fp:
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

    def render_text(
        self,
        img: Image.Image,
        text: str,
        margin: tuple[int, int] = (0, 0),
        line_padding: int = 0,
    ):
        img_width, img_height = img.size

        x, y = margin[0], margin[1] + self.ascent - 1

        for line in text.split("\n"):
            for word in line.split(" "):
                width = 0
                for char in word:
                    code_point = ord(char)
                    glyph = self.get_glyph(code_point)

                    if glyph is None:
                        continue

                    # +1
                    width += glyph.x_advance

                if x + width + margin[0] - 1 > img_width:
                    x = margin[0]
                    y += self.ascent + self.descent + line_padding

                if y + self.descent + margin[1] + line_padding > img_height - 1:
                    break

                for char in word:
                    code_point = ord(char)
                    glyph = self.get_glyph(code_point)

                    if glyph is None:
                        continue

                    self.render_glyph(img, (x, y), glyph)
                    # +1
                    x += glyph.x_advance

                glyph = self.get_glyph(32)
                if (glyph is not None) and not (
                    # +1
                    x + glyph.x_advance + margin[0] - 1 > img_width
                ):
                    self.render_glyph(img, (x, y), glyph)
                    # +1
                    x += glyph.x_advance

            x = margin[0]
            y += self.ascent + self.descent + line_padding

            if y + self.descent + margin[1] + line_padding > img_height - 1:
                break

    def render_glyph(
        self, img: Image.Image, baseline_origin: tuple[int, int], glyph: Glyph
    ):
        for bmp_y in range(0, glyph.bbox[1]):
            for bmp_x in range(0, glyph.bbox[0]):
                x = bmp_x + baseline_origin[0] + glyph.bbox[2]
                y = bmp_y + baseline_origin[1] - glyph.bbox[1] - glyph.bbox[3] + 1

                if glyph.bitmap[bmp_x // 8 + (bmp_y * math.ceil(glyph.bbox[0] / 8))] & (
                    1 << (7 - (bmp_x % 8))
                ):
                    img.putpixel((x, y), 0)

    def get_glyph_array(self) -> list[Glyph]:
        return self.glyphs

    def get_glyph(self, code_point) -> Glyph | None:
        for glyph in self.glyphs:
            if glyph.code_point == code_point:
                return glyph


TEXT = ""
with open("./book.txt") as fp:
    TEXT = fp.read()

min_codepoint = min(ord(char) for char in TEXT)
max_codepoint = max(ord(char) for char in TEXT)

print(min_codepoint, max_codepoint)

folder = Path("/Users/bhuvansh/Desktop/edp_test")
for bdf_file in folder.glob("*.bdf"):
    font = BDF_Font(f"./{bdf_file.name}")
    img = Image.new("1", (480, 648), 1)
    font.render_text(img, TEXT[2000:], (10, 20))
    img.save(f"{bdf_file.name}.png")
