import pytest
from playwright.sync_api import expect

from tests.conftest import api_user1, wallets_page
from utilities.money import ui_amount_to_minor

pytestmark = pytest.mark.regression

ALL_CURRENCIES = {"ILS", "USD", "EUR", "GBP"}
SWAP_AMOUNT = "100"


class TestWalletsPositive:
    pytestmark = pytest.mark.positive

    # Every wallet card and the total balance show the amounts stored on the server.
    @pytest.mark.smoke
    def test_wallets_and_total_match_server(self, wallets_page, api_user1):
        wallets = api_user1.wallets()

        assert wallets_page.shown_currencies() == set(wallets)
        for currency, balance in wallets.items():
            assert wallets_page.balance_minor(currency) == balance
        assert wallets_page.total_minor() == api_user1.wallet_summary()["total_minor"]

    # The conversion preview shows the same result as the server calculates.
    @pytest.mark.parametrize("amount", ["1", "100", "1,234.56", "1000000"])
    def test_conversion_preview_matches_server(self, wallets_page, api_user1, amount):
        frm, to = wallets_page.preview_currencies()

        wallets_page.set_preview_amount(amount)

        expected = api_user1.preview(ui_amount_to_minor(amount), frm, to)["receiving_amount_minor"]
        wallets_page.expect_preview_result(expected)

    # Swap reverses the currencies, and the result is recalculated in the new direction.
    def test_swap_reverses_the_conversion(self, wallets_page, api_user1):
        frm, to = wallets_page.preview_currencies()
        wallets_page.set_preview_amount(SWAP_AMOUNT)

        wallets_page.swap()

        assert wallets_page.preview_currencies() == (to, frm)
        expected = api_user1.preview(ui_amount_to_minor(SWAP_AMOUNT), to, frm)["receiving_amount_minor"]
        wallets_page.expect_preview_result(expected)

    # Every exchange rate shown equals the server's current rate.
    def test_rates_match_server(self, wallets_page, api_user1):
        base = api_user1.preferred_currency()
        rates = api_user1.cross_rates(base)

        shown = wallets_page.shown_rates()

        assert set(shown) == set(rates)
        for currency, rate in rates.items():
            assert shown[currency] == pytest.approx(rate, abs=1e-6)


class TestWalletsNegative:
    pytestmark = pytest.mark.negative

    # A huge amount shows the same limit message as any amount above 1,000,000.00 (known bug: it shows "Amount is too large.").
    @pytest.mark.xfail(reason='Known bug: a huge amount shows "Amount is too large." instead of the allowed range', strict=True, raises=AssertionError)
    def test_huge_amount_shows_the_limit_message(self, wallets_page):
        wallets_page.set_preview_amount("100000000000000")
        
        expect(wallets_page.preview_errors).to_have_text(["Enter an amount between 0.01 and 1,000,000.00."])

    # An invalid amount in the conversion preview shows an error and no result.
    @pytest.mark.parametrize(("amount", "error"), [
        ("abc", "Enter a valid positive number."),
        ("-5", "Enter a valid positive number."),
        ("1e3", "Enter a valid positive number."),
        ("0", "Amount must be greater than zero."),
        ("1.234", "Use at most 2 decimal places."),
    ], ids=["letters", "negative", "scientific", "zero", "three-decimals"])
    def test_invalid_amount(self, wallets_page, amount, error):
        wallets_page.set_preview_amount(amount)

        expect(wallets_page.preview_error(error)).to_be_visible()
        wallets_page.expect_no_preview_result()

    # An amount above the 1,000,000.00 limit is rejected by the server.
    def test_amount_above_limit(self, wallets_page):
        wallets_page.set_preview_amount("1000000.01")

        expect(wallets_page.preview_errors).to_have_text("Enter an amount between 0.01 and 1,000,000.00.")
        wallets_page.expect_no_preview_result()

    # When the user already has a wallet in every currency, "Add wallet" is disabled.
    def test_add_wallet_disabled_when_all_currencies_exist(self, wallets_page, api_user1):
        for currency in ALL_CURRENCIES - set(api_user1.wallets()):
            api_user1.add_wallet(currency)
        wallets_page.open()

        assert wallets_page.shown_currencies() == ALL_CURRENCIES
        expect(wallets_page.add_wallet_button).to_be_disabled()
