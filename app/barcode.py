"""PDF417 barcode image generation."""
from PIL import Image
from pdf417gen import encode, render_image


def generate_pdf417_image(
    text: str,
    columns: int = 6,
    security_level: int = 2,
    scale: int = 3,
    ratio: int = 3,
    padding: int = 10,
) -> Image.Image:
    codes = encode(text, columns=columns, security_level=security_level, encoding="utf-8")
    return render_image(codes, scale=scale, ratio=ratio, padding=padding)
