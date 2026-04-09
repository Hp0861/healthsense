"""
generate_sample_image.py – Creates a PNG lab report image from the sample text.

Run once before testing:
    python data/generate_sample_image.py
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SAMPLE_TEXT = Path(__file__).parent / "sample_report.txt"
OUT_IMAGE   = Path(__file__).parent / "sample_report.png"


def generate():
    text = SAMPLE_TEXT.read_text()
    lines = text.splitlines()

    # Canvas dimensions
    W, H      = 900, max(600, len(lines) * 22 + 80)
    img       = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw      = ImageDraw.Draw(img)

    # Try to load a monospace font, fall back to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 16)
    except Exception:
        font = ImageFont.load_default()

    y = 30
    for line in lines:
        draw.text((30, y), line, fill=(20, 20, 20), font=font)
        y += 22

    img.save(str(OUT_IMAGE))
    print(f"✅  Sample image saved to: {OUT_IMAGE}")


if __name__ == "__main__":
    generate()
