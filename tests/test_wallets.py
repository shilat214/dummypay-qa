import re

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.regression

ALL_CURRENCIES = 4  # ILS, USD, EUR, GBP


class TestWalletsPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_wallets_page_shows_total_and_wallet_cards(self, wallets_page):
        wallets_page.expect_loaded()
        expect(wallets_page.total_balance).to_be_visible()
        expect(wallets_page.wallet_cards.first).to_be_visible()

    def test_add_wallet_dialog_offers_only_missing_currencies(self, wallets_page):
        owned = wallets_page.owned_wallets_count()
        if owned >= ALL_CURRENCIES:
            pytest.skip("User already owns every supported currency wallet.")
        wallets_page.open_add_wallet_dialog()
        expect(wallets_page.currency_options()).to_have_count(ALL_CURRENCIES - owned)

    def test_cancelling_add_wallet_does_not_create_a_wallet(self, wallets_page):
        owned = wallets_page.owned_wallets_count()
        if owned >= ALL_CURRENCIES:
            pytest.skip("Add wallet is disabled when every currency wallet exists.")
        wallets_page.add_wallet_button.click()
        wallets_page.dialog.get_by_role("button", name="Cancel").click()
        expect(wallets_page.dialog).to_be_hidden()
        expect(wallets_page.wallet_cards).to_have_count(owned)

    def test_conversion_preview_shows_a_converted_amount(self, wallets_page):
        wallets_page.set_preview_amount("100")
        expect(wallets_page.preview_result).to_have_text(re.compile(r"[₪$€£]\s?[\d,]+\.\d{2}"))


    @pytest.mark.smoke
    def test_new_wallet_is_created_with_zero_balance(self, wallets_page):
        owned = wallets_page.owned_wallets_count()
        if owned >= ALL_CURRENCIES:
            pytest.skip("No missing currency wallet left to add.")
        wallets_page.add_wallet_button.click()
        currency = wallets_page.choose_first_missing_currency()
        wallets_page.confirm_add_button.click()
        expect(wallets_page.text(f"{currency} wallet added.")).to_be_visible()
        expect(wallets_page.wallet_cards).to_have_count(owned + 1)
        expect(wallets_page.wallet_card(currency)).to_contain_text(re.compile(r"0\.00"))


class TestWalletsNegative:
    pytestmark = pytest.mark.negative

    def test_too_many_decimals_is_rejected(self, wallets_page):
        wallets_page.set_preview_amount("1.234")
        expect(wallets_page.preview.get_by_text("Use at most 2 decimal places.")).to_be_visible()

    def test_non_numeric_amount_is_rejected(self, wallets_page):
        wallets_page.set_preview_amount("abc")
        expect(wallets_page.preview.get_by_text("Enter a valid positive number.")).to_be_visible()

    def test_zero_amount_is_rejected(self, wallets_page):
        wallets_page.set_preview_amount("0")
        expect(wallets_page.preview.get_by_text("Amount must be greater than zero.")).to_be_visible()

    def test_cannot_confirm_new_wallet_without_choosing_a_currency(self, wallets_page):
        owned = wallets_page.owned_wallets_count()
        if owned >= ALL_CURRENCIES:
            pytest.skip("Add wallet is disabled when every currency wallet exists.")
        wallets_page.add_wallet_button.click()
        expect(wallets_page.confirm_add_button).to_be_disabled()
        expect(wallets_page.wallet_cards).to_have_count(owned)

    def test_add_wallet_button_is_disabled_when_every_currency_exists(self, wallets_page):
        if wallets_page.owned_wallets_count() < ALL_CURRENCIES:
            pytest.skip("User still has a missing currency, so Add wallet is enabled.")
        expect(wallets_page.add_wallet_button).to_be_disabled()
