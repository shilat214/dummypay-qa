"""Wallets page - UI tests (3 positive, 3 negative).

Each test checks what the page SHOWS against what the server actually HOLDS
(read through the API), so it verifies data correctness, not just that elements exist.
The API is used only as the source of truth (expected values).
"""
import pytest
from playwright.sync_api import expect

from utilities.money import ui_amount_to_minor

pytestmark = pytest.mark.regression

ALL_CURRENCIES = {"ILS", "USD", "EUR", "GBP"}


class TestWalletsPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_wallets_and_total_match_server(self, wallets_page, api_user1):
        """Every card shows the server balance, and the total equals the server summary."""
        server = api_user1.wallets()
        summary = api_user1.wallet_summary()

        assert wallets_page.shown_currencies() == set(server), "UI must show exactly the user's wallets"
        for currency, balance in server.items():
            assert wallets_page.balance_minor(currency) == balance, f"{currency} balance differs from server"
        assert wallets_page.total_minor() == summary["total_minor"]
        expect(wallets_page.total_balance).to_contain_text(f"shown in {summary['preferred_currency']}")

    @pytest.mark.parametrize("amount", ["1", "100", "1,234.56", "1000000"])
    def test_conversion_preview_and_swap_match_server(self, wallets_page, api_user1, amount):
        """Shown result equals the server's calculation, before and after swapping the pair."""
        frm, to = wallets_page.preview_currencies()
        minor = ui_amount_to_minor(amount)

        wallets_page.set_preview_amount(amount)
        wallets_page.expect_preview_result(api_user1.preview(minor, frm, to)["receiving_amount_minor"])

        wallets_page.swap_button.click()
        assert wallets_page.preview_currencies() == (to, frm)
        wallets_page.expect_preview_result(api_user1.preview(minor, to, frm)["receiving_amount_minor"])

    def test_rates_card_matches_server_rates(self, wallets_page, api_user1):
        """Every rate shown for the preferred currency equals the server's live rate."""
        base = api_user1.profile()["preferred_currency"]
        server = api_user1.cross_rates(base)

        shown = wallets_page.shown_rates()

        assert set(shown) == set(server), "UI must list exactly the server's currency pairs"
        for currency, rate in server.items():
            # The UI shows up to 6 decimals, so allow a difference in the last displayed digit.
            assert shown[currency] == pytest.approx(rate, abs=1e-6), f"1 {base} -> {currency}"
        expect(wallets_page.rates_card).to_contain_text("Last updated")


class TestWalletsNegative:
    pytestmark = pytest.mark.negative

    @pytest.mark.parametrize(
        ("amount", "error"),
        [
            ("abc", "Enter a valid positive number."),
            ("-5", "Enter a valid positive number."),
            ("1e3", "Enter a valid positive number."),
            ("0", "Amount must be greater than zero."),
            ("0.00", "Amount must be greater than zero."),
            ("1.234", "Use at most 2 decimal places."),
        ],
        ids=["letters", "negative", "scientific", "zero", "zero-decimals", "three-decimals"],
    )
    def test_invalid_preview_amount_is_rejected_client_side(self, wallets_page, amount, error):
        """All client-side validation rules of the amount field, grouped in one test."""
        wallets_page.set_preview_amount(amount)

        expect(wallets_page.preview.get_by_text(error)).to_be_visible()
        expect(wallets_page.preview_amount).to_have_attribute("aria-invalid", "true")
        wallets_page.expect_no_preview_result()

    def test_amount_above_limit_is_rejected_by_server(self, wallets_page):
        """1,000,000.01 passes the browser checks, so only the server can reject it."""
        wallets_page.set_preview_amount("1000000.01")

        expect(wallets_page.preview_server_error).to_have_text("Enter an amount between 0.01 and 1,000,000.00.")
        wallets_page.expect_no_preview_result()

    def test_add_wallet_never_offers_an_owned_currency(self, wallets_page, api_user1):
        """The dialog offers only missing currencies; with all four owned the button is disabled."""
        owned = set(api_user1.wallets())

        if owned == ALL_CURRENCIES:
            expect(wallets_page.add_wallet_button).to_be_disabled()
        else:
            offered = set(wallets_page.offered_currencies())
            assert offered == ALL_CURRENCIES - owned
            assert not (offered & owned)
