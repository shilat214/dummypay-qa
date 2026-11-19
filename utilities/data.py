"""Static test data."""
import uuid

# Card given in the assignment: 4111 1111 1111 1111  03/30  737
VALID_VISA = {"name": "QA Tester", "number": "4111111111111111", "expiry": "0330",
              "cvv": "737", "brand": "Visa", "last4": "1111", "shown_expiry": "Exp 03/30"}
VALID_MASTERCARD = {"name": "QA Tester", "number": "5555555555554444", "expiry": "1230",
                    "cvv": "123", "brand": "Mastercard", "last4": "4444", "shown_expiry": "Exp 12/30"}
VALID_AMEX = {"name": "QA Tester", "number": "378282246310005", "expiry": "1230",
              "cvv": "1234", "brand": "American Express", "last4": "0005", "shown_expiry": "Exp 12/30"}
TEST_CARD_LAST4 = ["1111", "4444", "0005"]

INVALID_LUHN_NUMBER = "4242424242424241"
EXPIRED_EXPIRY = "0120"

BANK_NAME = "QA Test Bank"
IBAN_GB_VALID = "GB82 WEST 1234 5698 7654 32"
IBAN_GB_BAD_CHECKSUM = "GB82 WEST 1234 5698 7654 33"
IBAN_GB_TOO_SHORT = "GB82 WEST 1234 5698 7654"
IBAN_DE_VALID = "DE89 3704 0044 0532 0130 00"


def unknown_email() -> str:
    """An address that is certainly not a registered user."""
    return f"nobody-{uuid.uuid4().hex[:10]}@test.dummypay.dev"
