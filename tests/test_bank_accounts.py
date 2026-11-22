import pytest
from playwright.sync_api import expect

from utilities.data import (BANK_NAME, IBAN_DE_VALID, IBAN_GB_BAD_CHECKSUM,
                            IBAN_GB_TOO_SHORT, IBAN_GB_VALID)

pytestmark = pytest.mark.regression

HOLDER = "QA Tester"


def _add_and_verify(bank_page, country, currency, identifier, expected_mask):
    bank_page.add_account(HOLDER, BANK_NAME, country, currency, identifier)
    expect(bank_page.dialog).to_be_hidden(timeout=20_000)  # server may be slow (cold start)
    expect(bank_page.toast("Simulated bank account added.")).to_be_visible()
    item = bank_page.item_by_bank(BANK_NAME)
    expect(item).to_have_count(1)
    expect(item).to_contain_text(f"{country} · {currency}")
    expect(item).to_contain_text(expected_mask)
    expect(item).to_contain_text("Simulated")
    bank_page.remove_account(BANK_NAME)
    expect(bank_page.item_by_bank(BANK_NAME)).to_have_count(0)


class TestBankAccountsPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_page_loads(self, bank_page):
        bank_page.expect_loaded()

    @pytest.mark.smoke
    def test_uk_account_with_valid_iban_is_added_and_masked(self, bank_page):
        _add_and_verify(bank_page, "United Kingdom", "GBP", IBAN_GB_VALID, "IBAN GB•• •••• 5432")

    def test_german_account_with_valid_iban_is_added(self, bank_page):
        _add_and_verify(bank_page, "Germany", "EUR", IBAN_DE_VALID, "IBAN DE•• •••• 3000")

    def test_us_account_number_without_iban_is_added(self, bank_page):
        _add_and_verify(bank_page, "United States", "USD", "123456789", "•••• 6789")


class TestBankAccountsNegative:
    pytestmark = pytest.mark.negative

    def test_iban_with_bad_checksum_is_rejected(self, bank_page):
        bank_page.add_account(HOLDER, BANK_NAME, "United Kingdom", "GBP", IBAN_GB_BAD_CHECKSUM)
        expect(bank_page.dialog.get_by_text("IBAN is not valid (checksum failed).")).to_be_visible()

    def test_iban_with_wrong_length_is_rejected(self, bank_page):
        bank_page.add_account(HOLDER, BANK_NAME, "United Kingdom", "GBP", IBAN_GB_TOO_SHORT)
        expect(bank_page.dialog.get_by_text("A United Kingdom IBAN has 22 characters.")).to_be_visible()

    def test_iban_country_must_match_selected_country(self, bank_page):
        bank_page.add_account(HOLDER, BANK_NAME, "United Kingdom", "GBP", IBAN_DE_VALID)
        expect(bank_page.dialog.get_by_text("IBAN country code must match United Kingdom (GB).")).to_be_visible()

    def test_too_short_account_number_is_rejected(self, bank_page):
        bank_page.add_account(HOLDER, BANK_NAME, "United States", "USD", "12")
        expect(bank_page.dialog.get_by_text("Enter an IBAN or an account number of 4–20 digits.")).to_be_visible()

    def test_empty_account_holder_is_rejected(self, bank_page):
        bank_page.add_account("", BANK_NAME, "United States", "USD", "123456789")
        expect(bank_page.dialog.get_by_text("Account holder name must be 2–100 characters.")).to_be_visible()
