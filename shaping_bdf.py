from PIL import Image, ImageDraw, ImageFont
import os

# Settings
char = "क्ष"  # Devanagari conjunct (3 code points: क, ्, ष)
font_path = "/mnt/c/Users/bhuva/Downloads/Noto_Sans/static/NotoSans-Medium.ttf"  # Replace with your TTF font file path
font_size_pt = 14  # 12-point font
dpi = 138  # Target resolution
output_bdf = "ksha.bdf"  # Output file

# Convert pt to pixels
font_size_px = int(font_size_pt * dpi / 72)  # 12pt @ 138DPI = 23px

# Load font
try:
    font = ImageFont.truetype(font_path, font_size_px)
except IOError:
    raise SystemExit(f"Error: Font file not found at {font_path}")

# Render glyph with padding
img = Image.new("1", (font_size_px * 3, font_size_px * 3), 0)  # Extra space
draw = ImageDraw.Draw(img)
draw.text((0, 0), char, fill=1, font=font)

# Crop to visible glyph
bbox = img.getbbox()
if not bbox:
    raise SystemExit("Error: Glyph not rendered (empty bbox)")

glyph_img = img.crop(bbox)
width, height = glyph_img.size


# Convert pixels to BDF hex
def pixels_to_hex(pixels, width):
    hex_str = ""
    for i in range(0, width, 8):
        byte = 0
        for bit in range(8):
            if i + bit < width and pixels[i + bit]:
                byte |= 1 << (7 - bit)
        hex_str += f"{byte:02X}"
    return hex_str


pixels = list(glyph_img.getdata())
pixels = [pixels[i * width : (i + 1) * width] for i in range(height)]
hex_bitmap = [pixels_to_hex(row, width) for row in pixels]

# Use PUA (Private Use Area) codepoint since "क्ष" is multi-codepoint
encoding = 0xE000  # First PUA codepoint (adjust if needed)

# Generate BDF
bdf_content = (
    f"""STARTFONT 2.1
FONT {os.path.basename(font_path).replace(".ttf", "")}-ksha-12pt
SIZE {font_size_pt} {dpi} {dpi}
FONTBOUNDINGBOX {width} {height} 0 0
STARTPROPERTIES 2
FONT_ASCENT {height}
FONT_DESCENT 0
ENDPROPERTIES

STARTCHAR ksha
ENCODING {encoding}
SWIDTH {width * 10} 0
DWIDTH {width} 0
BBX {width} {height} 0 0
BITMAP
"""
    + "\n".join(hex_bitmap)
    + "\nENDCHAR\nENDFONT"
)

# Save file
with open(output_bdf, "w", encoding="utf-8") as f:
    f.write(bdf_content)

print(f"BDF file saved as {output_bdf} (12pt at 138DPI)")
