from app.api.customers import normalize_contact
from app.modules.models import ContactType


def test_indian_mobile_number_normalizes_to_e164():
    assert normalize_contact(ContactType.phone, "9876543210", "IN") == "+919876543210"


def test_email_normalization():
    assert normalize_contact(ContactType.email, " Sales@Example.COM ") == "sales@example.com"
