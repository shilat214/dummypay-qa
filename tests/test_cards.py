from datetime import date

import pytest
from playwright.sync_api import expect

from utilities.data import (EXPIRED_EXPIRY, INVALID_LUHN_NUMBER, VALID_AMEX,
                            VALID_MASTERCARD, VALID_VISA)

pytestmark = pytest.mark.regression

HOLDER = VALID_VISA["name"]
TOO_FAR_EXPIRY = f"12{(date.today().year + 21) % 100:02d}"


# Creates the assignment's Visa card through the API and reloads the page so it is shown.
@pytest.fixture
def existing_card(cards_page, api_user1):
    card = api_user1.add_card(HOLDER, VALID_VISA["number"], "03/30", VALID_VISA["cvv"])
    cards_page.open()
    return card


# Submits the form and checks that the error is shown and nothing is saved on the server.
def _expect_rejected(cards_page, api, name, number, expiry, cvv, message):
    before = api.cards()
    cards_page.add_card(name, number, expiry, cvv)
    expect(cards_page.error(message)).to_be_visible()
    assert api.cards() == before


class TestCardsPositive:
    pytestmark = pytest.mark.positive

    # The page shows exactly the cards stored on the server.
    @pytest.mark.smoke
    def test_page_shows_all_server_cards(self, cards_page, api_user1, existing_card):
        cards = api_user1.cards()
        expect(cards_page.items).to_have_count(len(cards))
        for card in cards:
            expect(cards_page.item_by_last4(card["last_four_digits"]).first).to_be_visible()

    # An added card is shown, the server stores only its last 4 digits, and other cards stay.
    @pytest.mark.parametrize("card", [VALID_VISA, VALID_MASTERCARD, VALID_AMEX],
                             ids=["visa", "mastercard", "amex"])
    def test_add_card(self, cards_page, api_user1, card):
        before = api_user1.cards()

        cards_page.add_card(card["name"], card["number"], card["expiry"], card["cvv"])

        expect(cards_page.toast("Simulated card added.")).to_be_visible(timeout=20_000)
        item = cards_page.item_by_last4(card["last4"])
        expect(item).to_contain_text(card["brand"])
        expect(item).to_contain_text(f"•••• •••• •••• {card['last4']}")
        expect(item).to_contain_text(card["shown_expiry"])
        after = api_user1.cards()
        new = [c for c in after if c not in before]
        assert len(after) == len(before) + 1 and len(new) == 1
        assert new[0]["last_four_digits"] == card["last4"]
        assert card["number"] not in str(new[0])

    # A removed card disappears from the page and the server, and other cards stay.
    def test_remove_card(self, cards_page, api_user1, existing_card):
        before = api_user1.cards()

        cards_page.remove_card(existing_card["last_four_digits"])

        expect(cards_page.toast("Card removed.")).to_be_visible()
        expect(cards_page.item_by_last4(existing_card["last_four_digits"])).to_have_count(0)
        assert api_user1.cards() == [c for c in before if c["id"] != existing_card["id"]]


    # While typing, the dialog recognises the card brand and groups the digits.
    @pytest.mark.parametrize(("card", "shown_number"), [
        (VALID_VISA, "4111 1111 1111 1111"),
        (VALID_MASTERCARD, "5555 5555 5555 4444"),
        (VALID_AMEX, "3782 822463 10005"),
    ], ids=["visa", "mastercard", "amex"])
    def test_brand_is_recognised_while_typing(self, cards_page, card, shown_number):
        cards_page.open_add_dialog()

        cards_page.card_number_input.fill(card["number"])

        expect(cards_page.card_number_input).to_have_value(shown_number)
        expect(cards_page.dialog.get_by_text(card["brand"], exact=True)).to_be_visible()


class TestCardsNegative:
    pytestmark = pytest.mark.negative

    # An invalid card number is rejected.
    @pytest.mark.parametrize(("number", "message"), [
        (INVALID_LUHN_NUMBER, "Card number is not valid (checksum failed)."),
        ("411111111111", "Card number has an invalid length for Visa."),
    ], ids=["bad-checksum", "12-digit-visa"])
    def test_invalid_card_number(self, cards_page, api_user1, number, message):
        _expect_rejected(cards_page, api_user1, HOLDER, number, "1230", "123", message)

    # An expiry date that is in the past, not a real month, or over 20 years ahead is rejected.
    @pytest.mark.parametrize(("expiry", "message"), [
        (EXPIRED_EXPIRY, "This card has expired."),
        ("1330", "Expiry must be in MM/YY format."),
        (TOO_FAR_EXPIRY, "Expiry date is too far in the future."),
    ], ids=["expired", "month-13", "over-20-years"])
    def test_invalid_expiry(self, cards_page, api_user1, expiry, message):
        _expect_rejected(cards_page, api_user1, HOLDER, VALID_VISA["number"], expiry, "123", message)

    # A CVV with the wrong number of digits for the card brand is rejected.
    @pytest.mark.parametrize(("card", "cvv", "message"), [
        (VALID_VISA, "12", "CVV must be 3 digits."),
        (VALID_AMEX, "123", "CVV must be 4 digits."),
    ], ids=["visa-2-digits", "amex-3-digits"])
    def test_invalid_cvv(self, cards_page, api_user1, card, cvv, message):
        _expect_rejected(cards_page, api_user1, HOLDER, card["number"], "1230", cvv, message)
