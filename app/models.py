"""Recipient profile and payer domain models, and the glue to build a PaymentSlip."""
from dataclasses import dataclass

from app.hub3a import PaymentSlip


@dataclass
class RecipientProfile:
    name: str
    address: str
    place: str
    iban: str


@dataclass
class Payer:
    name: str
    address: str
    place: str
    amount: float
    model: str = "HR00"
    reference: str = ""
    purpose_code: str = ""
    description: str = ""
    id: int | None = None


def build_slip(recipient: RecipientProfile, payer: Payer) -> PaymentSlip:
    return PaymentSlip(
        payer_name=payer.name,
        payer_address=payer.address,
        payer_place=payer.place,
        recipient_name=recipient.name,
        recipient_address=recipient.address,
        recipient_place=recipient.place,
        recipient_iban=recipient.iban,
        amount=payer.amount,
        model=payer.model,
        reference=payer.reference,
        purpose_code=payer.purpose_code,
        description=payer.description,
    )


def recipient_from_row(row) -> RecipientProfile:
    return RecipientProfile(
        name=row["name"],
        address=row["address"],
        place=row["place"],
        iban=row["iban"],
    )


def payer_from_row(row) -> Payer:
    return Payer(
        id=row["id"],
        name=row["name"],
        address=row["address"],
        place=row["place"],
        amount=row["amount"],
        model=row["model"],
        reference=row["reference"],
        purpose_code=row["purpose_code"],
        description=row["description"],
    )
