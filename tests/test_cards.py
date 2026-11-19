import pytest
from playwright.sync_api import expect

from utilities.data import (EXPIRED_EXPIRY, INVALID_LUHN_NUMBER, VALID_AMEX,
                            VALID_MASTERCARD, VALID_VISA)

pytestmark = pytest.mark.regression


def _add_and_verify(cards_page, card):
    cards_page.add_card(card["name"], card["number"], card["expiry"], card["cvv"])
    expect(cards_page.toast("Simulated card added.")).to_be_visible()
    item = cards_page.item_by_last4(card["last4"])
    expect(item).to_have_count(1)
    expect(item).to_contain_text(card["brand"])
    expect(item).to_contain_text(f"•••• •••• •••• {card['last4']}")
    expect(item).to_contain_text(card["shown_expiry"])
    expect(item).to_contain_text("Simulated")
    cards_page.remove_card(card["last4"])
    expect(cards_page.item_by_last4(card["last4"])).to_have_count(0)


class TestCardsPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_page_loads_and_says_cards_are_simulated(self, cards_page):
        cards_page.expect_loaded()
        expect(cards_page.disclaimer).to_be_visible()

    @pytest.mark.smoke
    def test_assignment_visa_card_can_be_added_and_removed(self, cards_page):
        _add_and_verify(cards_page, VALID_VISA)

    def test_mastercard_is_detected_and_added(self, cards_page):
        _add_and_verify(cards_page, VALID_MASTERCARD)

    def test_amex_with_four_digit_cvv_is_accepted(self, cards_page):
        _add_and_verify(cards_page, VALID_AMEX)


class TestCardsNegative:
    pytestmark = pytest.mark.negative

    def test_number_failing_luhn_is_rejected(self, cards_page):
        cards_page.add_card("QA Tester", INVALID_LUHN_NUMBER, "1230", "123")
        expect(cards_page.dialog.get_by_text("Card number is not valid (checksum failed).")).to_be_visible()

    def test_expired_card_is_rejected(self, cards_page):
        cards_page.add_card("QA Tester", VALID_VISA["number"], EXPIRED_EXPIRY, "123")
        expect(cards_page.dialog.get_by_text("This card has expired.")).to_be_visible()

    def test_short_cvv_is_rejected(self, cards_page):
        cards_page.add_card("QA Tester", VALID_VISA["number"], "1230", "12")
        expect(cards_page.dialog.get_by_text("CVV must be 3 digits.")).to_be_visible()

    def test_wrong_length_visa_number_is_rejected(self, cards_page):
        cards_page.add_card("QA Tester", "411111111111", "1230", "123")
        expect(cards_page.dialog.get_by_text("Card number has an invalid length for Visa.")).to_be_visible()

    def test_empty_cardholder_name_is_rejected(self, cards_page):
        cards_page.add_card("", VALID_VISA["number"], "1230", "123")
        expect(cards_page.dialog.get_by_text("Cardholder name must be 2–100 characters.")).to_be_visible()
