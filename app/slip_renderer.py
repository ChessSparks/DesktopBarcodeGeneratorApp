"""Renders a filled-in HUB3 uplatnica by overlaying text and a PDF417 barcode
onto the uplatnica.png template.

Field coordinates are pixel positions measured directly against the reference
template image (2475x1006). If a differently-sized template is ever swapped
in, coordinates are scaled proportionally.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.barcode import generate_pdf417_image
from app.hub3a import PaymentSlip, to_barcode_string

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
TEMPLATE_PATH = ASSETS_DIR / "uplatnica.png"

REFERENCE_SIZE = (2475, 1006)
FONT_PATH = "C:/Windows/Fonts/arial.ttf"

DEFAULT_FONT_SIZE = 32
SMALL_FONT_SIZE = 20

# left/top/width/height are pixel coordinates measured against REFERENCE_SIZE.
FIELD_LAYOUT = {
    "payer_name": dict(left=60, top=110, width=520, height=65),
    "payer_address": dict(left=60, top=180, width=520, height=65),
    "payer_place": dict(left=60, top=250, width=520, height=65),
    "currency": dict(left=900, top=70, width=130, height=55),
    "amount": dict(left=1160, top=70, width=700, height=55, align="right", letter_spacing=8),
    "iban": dict(left=850, top=310, width=1000, height=56, letter_spacing=21),
    "recipient_name": dict(left=60, top=355, width=520, height=100),
    "recipient_address": dict(left=60, top=461, width=520, height=100),
    "recipient_place": dict(left=60, top=567, width=520, height=90),
    "model": dict(left=610, top=405, width=170, height=58, letter_spacing=18),
    "reference": dict(left=850, top=405, width=1010, height=58),
    "purpose_code": dict(left=580, top=515, width=200, height=55),
    "description": dict(left=980, top=480, width=900, height=50),
    "amount_r": dict(left=2050, top=62, width=415, height=68, align="right", font_size=SMALL_FONT_SIZE),
    "iban_r": dict(left=2150, top=311, width=315, height=57, font_size=SMALL_FONT_SIZE),
    "model_reference_r": dict(left=2270, top=405, width=195, height=58, font_size=SMALL_FONT_SIZE),
    "description_r": dict(left=2010, top=480, width=455, height=180, font_size=SMALL_FONT_SIZE),
}

BARCODE_BOX = dict(left=70, top=700, width=650)


def _resolve_box(field: dict, scale_x: float, scale_y: float) -> tuple[float, float, float, float]:
    left = field["left"] * scale_x
    top = field["top"] * scale_y
    width = field["width"] * scale_x
    height = field["height"] * scale_y
    return left, top, width, height


def _draw_text_with_spacing(draw: ImageDraw.ImageDraw, x: float, y: float, text: str, font, spacing: float, fill):
    cursor = x
    for char in text:
        draw.text((cursor, y), char, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), char, font=font)
        char_width = (bbox[2] - bbox[0]) if char != " " else font.size * 0.3
        cursor += char_width + spacing


def _text_width_with_spacing(draw: ImageDraw.ImageDraw, text: str, font, spacing: float) -> float:
    total = 0.0
    for char in text:
        bbox = draw.textbbox((0, 0), char, font=font)
        char_width = (bbox[2] - bbox[0]) if char != " " else font.size * 0.3
        total += char_width + spacing
    return total - spacing if text else 0.0


def _draw_field(draw: ImageDraw.ImageDraw, key: str, text: str, scale_x: float, scale_y: float):
    if not text:
        return
    field = FIELD_LAYOUT[key]
    left, top, width, height = _resolve_box(field, scale_x, scale_y)
    avg_scale = (scale_x + scale_y) / 2
    font_size = round(field.get("font_size", DEFAULT_FONT_SIZE) * avg_scale)
    font = ImageFont.truetype(FONT_PATH, font_size)
    spacing = field.get("letter_spacing", 0) * avg_scale

    bbox = draw.textbbox((0, 0), "Ag", font=font)
    text_height = bbox[3] - bbox[1]
    y = top + (height - text_height) / 2

    if field.get("align") == "right":
        text_width = _text_width_with_spacing(draw, text, font, spacing)
        x = left + width - text_width
    else:
        x = left

    _draw_text_with_spacing(draw, x, y, text, font, spacing, fill=(0, 0, 0))


def render_filled_slip(slip: PaymentSlip, template_path: Path = TEMPLATE_PATH) -> Image.Image:
    image = Image.open(template_path).convert("RGB")
    scale_x = image.width / REFERENCE_SIZE[0]
    scale_y = image.height / REFERENCE_SIZE[1]
    draw = ImageDraw.Draw(image)

    amount_field = f"{slip.amount:,.2f}".replace(",", " ")
    model_reference_r = f"{slip.model} {slip.reference}".strip()

    values = {
        "payer_name": slip.payer_name,
        "payer_address": slip.payer_address,
        "payer_place": slip.payer_place,
        "currency": "EUR",
        "amount": amount_field,
        "amount_r": amount_field,
        "iban": slip.recipient_iban,
        "iban_r": slip.recipient_iban,
        "recipient_name": slip.recipient_name,
        "recipient_address": slip.recipient_address,
        "recipient_place": slip.recipient_place,
        "model": slip.model,
        "reference": slip.reference,
        "model_reference_r": model_reference_r,
        "purpose_code": slip.purpose_code,
        "description": slip.description,
        "description_r": slip.description,
    }
    for key, text in values.items():
        _draw_field(draw, key, text, scale_x, scale_y)

    barcode_text = to_barcode_string(slip)
    barcode_image = generate_pdf417_image(barcode_text)

    target_width = BARCODE_BOX["width"] * scale_x
    aspect = barcode_image.width / barcode_image.height
    target_height = target_width / aspect
    barcode_image = barcode_image.resize((round(target_width), round(target_height)))

    barcode_left = BARCODE_BOX["left"] * scale_x
    barcode_top = BARCODE_BOX["top"] * scale_y
    image.paste(barcode_image, (round(barcode_left), round(barcode_top)))

    return image
