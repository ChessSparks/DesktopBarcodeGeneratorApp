"""HUB3A payment slip encoding (Croatian HUB-3 PDF417 2D barcode standard)."""
from dataclasses import dataclass

HEADER = "HRVHUB30"
CURRENCY = "EUR"

MAX_LENGTHS = {
    "payer_name": 30,
    "payer_address": 27,
    "payer_place": 27,
    "recipient_name": 25,
    "recipient_address": 25,
    "recipient_place": 27,
    "recipient_iban": 21,
    "model": 4,
    "reference": 22,
    "purpose_code": 4,
    "description": 35,
}


@dataclass
class PaymentSlip:
    payer_name: str
    payer_address: str
    payer_place: str
    recipient_name: str
    recipient_address: str
    recipient_place: str
    recipient_iban: str
    amount: float
    model: str = "HR00"
    reference: str = ""
    purpose_code: str = ""
    description: str = ""

    def validate(self) -> None:
        iban = self.recipient_iban.replace(" ", "")
        if not iban.upper().startswith("HR"):
            raise ValueError("Recipient IBAN must be a Croatian IBAN starting with HR")
        if self.amount is None or self.amount <= 0:
            raise ValueError("Amount must be greater than 0")
        if not self.recipient_name.strip():
            raise ValueError("Recipient name is required")


def _truncate(value: str, field: str) -> str:
    return (value or "")[: MAX_LENGTHS[field]]


def to_barcode_string(slip: PaymentSlip) -> str:
    """Builds the LF-separated HUB3A record, matching the HUB-3 (EUR) spec."""
    slip.validate()
    iban = slip.recipient_iban.replace(" ", "")
    amount_in_cents = round(slip.amount * 100)
    amount_field = str(amount_in_cents).zfill(15)

    fields = [
        HEADER,
        CURRENCY,
        amount_field,
        _truncate(slip.payer_name, "payer_name"),
        _truncate(slip.payer_address, "payer_address"),
        _truncate(slip.payer_place, "payer_place"),
        _truncate(slip.recipient_name, "recipient_name"),
        _truncate(slip.recipient_address, "recipient_address"),
        _truncate(slip.recipient_place, "recipient_place"),
        _truncate(iban, "recipient_iban"),
        _truncate(slip.model, "model"),
        _truncate(slip.reference, "reference"),
        _truncate(slip.purpose_code, "purpose_code"),
        _truncate(slip.description, "description"),
    ]
    return "\n".join(fields)
