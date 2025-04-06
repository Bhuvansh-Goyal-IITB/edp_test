from PIL import Image
import math


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
        self, img: Image.Image, text: str, margin: tuple[int, int] = (0, 0)
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

                    width += glyph.x_advance + 1

                if x + width + margin[0] - 1 > img_width:
                    x = margin[0]
                    y += self.ascent + self.descent

                if y + self.descent + margin[1] > img_height - 1:
                    break

                for char in word:
                    code_point = ord(char)
                    glyph = self.get_glyph(code_point)

                    if glyph is None:
                        continue

                    self.render_glyph(img, (x, y), glyph)
                    x += glyph.x_advance + 1

                glyph = self.get_glyph(32)
                if (glyph is not None) and not (
                    x + glyph.x_advance + margin[0] > img_width
                ):
                    self.render_glyph(img, (x, y), glyph)
                    x += glyph.x_advance + 1

            x = margin[0]
            y += self.ascent + self.descent

            if y + self.descent + margin[1] > img_height - 1:
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


font = BDF_Font("./garamond.bdf")
TEXT = """The abandoned observatory perched on Blackridge Mountain had been closed since the 1963 solar eclipse, when three astronomers vanished mid-observation. Park rangers chalked it up to bears, but the equipment left behind told a different story—the telescopes were trained not on the sky, but on the valley below, and all the film canisters were filled with photographs of the same oak tree.

When geology student Mateo Rivera broke in to retrieve a rare mineral sample from the basement, he found the walls covered in equations that made his skin prickle. They weren't celestial calculations, but topographical vectors... as if someone had been trying to map something buried beneath the mountain. The most disturbing part? The chalkboards had been recently updated.

His flashlight glinted off a metal hatch in the floor, its surface etched with warnings in six languages. The rusted bolt came loose with one firm twist. Cold air rushed up the ladder shaft, carrying a scent like wet pennies and ozone. His last rational thought was that no basement could possibly be this deep.

The rangers found Mateo's backpack at the hatch entrance, its contents neatly arranged: compass spinning wildly, rock samples pulsing with bioluminescence, and his field notebook filled with sketches of a spiraling stone structure that couldn't exist at such depths. The final page held only a single phrase, written over and over in trembling script: "THEY'RE STILL DOWN THERE WATCHING THE TREE."

The observatory was demolished in 2004, but hikers still report seeing flashes of light from the mountain at 3:17 AM—precisely when the missing astronomers' stopwatches had frozen. The oak tree thrives, though botanists note its growth rings don't match any known dendrochronological record. As for the hatch? Every attempt to pour concrete into it fails; by morning, the mixture is always bone dry and crumbles to dust at a touch.
"""

img = Image.new("1", (300, 400), 1)

font.render_text(img, TEXT, (10, 20))
img.save("output.png")
