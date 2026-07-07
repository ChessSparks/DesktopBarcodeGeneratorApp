import pytest

from app.hub3a import PaymentSlip, to_barcode_string


def make_slip(**overrides) -> PaymentSlip:
    defaults = dict(
        payer_name="Marko Marković",
        payer_address="Ulica 1",
        payer_place="10000 Zagreb",
        recipient_name="Tvrtka d.o.o.",
        recipient_address="Avenija 2",
        recipient_place="10000 Zagreb",
        recipient_iban="HR12 1001 0051 8630 0016 0",
        amount=125.50,
        model="HR00",
        reference="123456789",
        purpose_code="",
        description="Račun broj 42",
    )
    defaults.update(overrides)
    return PaymentSlip(**defaults)


def test_barcode_string_structure():
    slip = make_slip()
    text = to_barcode_string(slip)
    lines = text.split("\n")

    assert lines[0] == "HRVHUB30"
    assert lines[1] == "EUR"
    assert lines[2] == "000000000012550"
    assert lines[9] == "HR1210010051863000160"
    assert len(lines) == 14


def test_amount_is_zero_padded_to_15_digits():
    slip = make_slip(amount=5)
    text = to_barcode_string(slip)
    amount_field = text.split("\n")[2]
    assert amount_field == "000000000000500"
    assert len(amount_field) == 15


def test_fields_are_truncated_to_max_length():
    slip = make_slip(payer_name="A" * 50)
    text = to_barcode_string(slip)
    payer_name_field = text.split("\n")[3]
    assert len(payer_name_field) == 30


def test_invalid_iban_raises():
    slip = make_slip(recipient_iban="DE1234567890")
    with pytest.raises(ValueError):
        to_barcode_string(slip)


def test_negative_amount_raises():
    slip = make_slip(amount=-1)
    with pytest.raises(ValueError):
        to_barcode_string(slip)
