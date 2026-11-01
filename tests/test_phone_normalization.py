import pytest

from app.api.customers import normalize_contact
from app.modules.models import ContactType


def test_indian_mobile_number_normalizes_to_e164():
    assert normalize_contact(ContactType.phone, "9876543210", "IN") == "+919876543210"


def test_email_normalization():
    assert normalize_contact(ContactType.email, " Sales@Example.COM ") == "sales@example.com"

def test_us_phone_number_normalization():
    assert normalize_contact(
        ContactType.phone, "2025550123", "US"
    ) == "+12025550123"


def test_phone_number_with_leading_and_trailing_spaces():
    assert normalize_contact(
        ContactType.phone, " 9876543210 ", "IN"
    ) == "+919876543210"


def test_invalid_phone_number():
    with pytest.raises(ValueError):
        normalize_contact(ContactType.phone, "12345", "IN")


def test_empty_phone_number():
    with pytest.raises(ValueError):
        normalize_contact(ContactType.phone, "", "IN")


def test_invalid_region_code():
    with pytest.raises(ValueError):
        normalize_contact(ContactType.phone, "9876543210", "INVALID")


# Email normalization

def test_email_normalization():
    assert normalize_contact(
        ContactType.email, " Sales@Example.COM "
    ) == "sales@example.com"


def test_email_with_leading_and_trailing_spaces():
    assert normalize_contact(
        ContactType.email, "  admin@example.com  "
    ) == "admin@example.com"


def test_email_already_lowercase():
    assert normalize_contact(
        ContactType.email, "sales@example.com"
    ) == "sales@example.com"


def test_email_with_plus_addressing():
    assert normalize_contact(
        ContactType.email, "Sales+Lead@Example.COM"
    ) == "sales+lead@example.com"


def test_invalid_email_without_at_symbol():
    with pytest.raises(ValueError):
        normalize_contact(ContactType.email, "sales.example.com")


def test_invalid_email_without_domain():
    with pytest.raises(ValueError):
        normalize_contact(ContactType.email, "sales@")


def test_invalid_email_without_local_part():
    with pytest.raises(ValueError):
        normalize_contact(ContactType.email, "@example.com")


def test_empty_email():
    with pytest.raises(ValueError):
        normalize_contact(ContactType.email, "")