from PIL import Image, ImageDraw, ImageFont

# Settings
text = " ग्घ"  # Devanagari text
font_path = "/mnt/c/Users/bhuva/Downloads/Noto_Sans/static/NotoSans-Medium.ttf"  # Replace with your TTF font file path
font_size_pt = 12  # Font size in points
dpi = 138  # Resolution in DPI

# Convert font size from points to pixels
font_size_px = int(font_size_pt * dpi / 72)  # 12pt at 138 DPI ≈ 23px

# Create a blank image (size will be adjusted based on text)
background_color = "white"
text_color = "black"

# Load the font
try:
    font = ImageFont.truetype(font_path, font_size_px)
except IOError:
    raise SystemExit(f"Error: Font file not found at {font_path}")

# Get text dimensions
draw = ImageDraw.Draw(
    Image.new("1", (1, 1), background_color)
)  # Temp image for measurement
bbox = draw.textbbox((0, 0), text, font=font)
text_width_px = bbox[2] - bbox[0]
text_height_px = bbox[3] - bbox[1]

# Add some padding (e.g., 20% of text height)
padding_px = int(text_height_px * 0.2)
image_width_px = text_width_px + 2 * padding_px
image_height_px = text_height_px + 2 * padding_px

# Create the final image
image = Image.new("1", (image_width_px, image_height_px), background_color)
draw = ImageDraw.Draw(image)

# Draw text (centered)
x = (image_width_px - text_width_px) / 2
y = (image_height_px - text_height_px) / 2
draw.text((x, y), text, fill=text_color, font=font)

# Save with DPI metadata
output_path = "shaped.png"
image.save(output_path, dpi=(dpi, dpi))  # Sets both X and Y resolution
print(f"Image saved as {output_path} (12 pt at 138 DPI)")

# Optional: Display the image
image.show()
