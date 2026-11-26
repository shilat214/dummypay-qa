import re

import pytest
from playwright.sync_api import expect

from utilities.data import (BANK_HOLDER, BANK_NAME, DE_ACCOUNT, IBAN_DE_VALID, IBAN_GB_BAD_CHECKSUM,
                            IBAN_GB_TOO_SHORT, UK_ACCOUNT, US_ACCOUNT, US_ACCOUNT_NUMBER)

pytestmark = pytest.mark.regression


# Creates one test account through the API and reloads the page so it is shown.
@pytest.fixture
def existing_account(bank_page, api_user1):
    account = api_user1.add_bank_account(BANK_HOLDER, BANK_NAME, "US", "USD", US_ACCOUNT_NUMBER)
    bank_page.open()
    return account


# Submits the form and checks that the error is shown and nothing is saved on the server.
def _expect_rejected(bank_page, api, holder, bank, country, currency, identifier, message):
    before = api.bank_accounts()
    bank_page.add_account(holder, bank, country, currency, identifier)
    expect(bank_page.error(message)).to_be_visible()
    assert api.bank_accounts() == before


class TestBankAccountsPositive:
    pytestmark = pytest.mark.positive

    
    # The page shows exactly the accounts stored on the server.
    @pytest.mark.smoke
    def test_page_shows_all_server_accounts(self, bank_page, api_user1, existing_account):
        accounts = api_user1.bank_accounts()
        expect(bank_page.items).to_have_count(len(accounts))
        for account in accounts:
            item = bank_page.item_for(account["bank_name"], account["masked_account_identifier"])
            expect(item.first).to_be_visible()

    # An added account is shown, the server stores only its masked number, and other accounts stay.
    @pytest.mark.parametrize("account", [UK_ACCOUNT, DE_ACCOUNT, US_ACCOUNT],
                             ids=["uk-iban", "germany-iban", "us-account-number"])
    def test_add_account(self, bank_page, api_user1, account):
        before = api_user1.bank_accounts()

        bank_page.add_account(BANK_HOLDER, BANK_NAME, account["country"], account["currency"], account["identifier"])

        expect(bank_page.toast("Simulated bank account added.")).to_be_visible(timeout=20_000)
        expect(bank_page.item_for(BANK_NAME, account["masked"])).to_contain_text(
            f"{BANK_HOLDER} · {account['country']} · {account['currency']}")
        after = api_user1.bank_accounts()
        new = [a for a in after if a not in before]
        assert len(after) == len(before) + 1 and len(new) == 1
        assert new[0]["masked_account_identifier"] == account["masked"]
        assert account["identifier"].replace(" ", "") not in str(new[0])

    # A removed account disappears from the page and the server, and other accounts stay.
    def test_remove_account(self, bank_page, api_user1, existing_account):
        before = api_user1.bank_accounts()

        bank_page.remove_account(BANK_NAME)

        expect(bank_page.toast("Bank account removed.")).to_be_visible()
        expect(bank_page.item_by_bank(BANK_NAME)).to_have_count(0)
        assert api_user1.bank_accounts() == [a for a in before if a["id"] != existing_account["id"]]

    # Closing the add dialog with Cancel or X saves nothing.
    @pytest.mark.parametrize("button", ["Cancel", "Close"], ids=["cancel", "x"])
    def test_closing_the_dialog_saves_nothing(self, bank_page, api_user1, button):
        before = api_user1.bank_accounts()
        bank_page.open_add_dialog()
        bank_page.fill_account(BANK_HOLDER, BANK_NAME, "United States", "USD", US_ACCOUNT_NUMBER)

        bank_page.close_dialog(button)

        expect(bank_page.dialog).to_be_hidden()
        assert api_user1.bank_accounts() == before
        

class TestBankAccountsNegative:
    pytestmark = pytest.mark.negative
    
    # Adding an account that is already saved is rejected (known bug: the site saves it again).
    @pytest.mark.xfail(reason="Known bug: the same bank account can be added twice", strict=True, raises=AssertionError)
    def test_same_account_twice(self, bank_page, api_user1, existing_account):
        _expect_rejected(bank_page, api_user1, BANK_HOLDER, BANK_NAME, "United States", "USD", US_ACCOUNT_NUMBER,
                         re.compile("already", re.IGNORECASE))

    # Fixing a wrong field removes its error message (known bug: the message stays until the form is sent again).
    @pytest.mark.xfail(reason="Known bug: the error message stays after the field is fixed, until the form is sent again", strict=True, raises=AssertionError)
    def test_error_disappears_after_fixing_the_field(self, bank_page):
        bank_page.open_add_dialog()
        bank_page.fill_account("QA Tester 2", BANK_NAME, "United States", "USD", US_ACCOUNT_NUMBER)
        bank_page.submit()
        error = bank_page.error("Account holder name may only contain letters, spaces, and . ' -")
        expect(error).to_be_visible()

        bank_page.holder_input.fill(BANK_HOLDER)

        expect(error).to_be_hidden()
        
    # An invalid IBAN or account number is rejected.
    @pytest.mark.parametrize(("country", "currency", "identifier", "message"), [
        ("United Kingdom", "GBP", IBAN_GB_BAD_CHECKSUM, "IBAN is not valid (checksum failed)."),
        ("United Kingdom", "GBP", IBAN_GB_TOO_SHORT, "A United Kingdom IBAN has 22 characters."),
        ("United Kingdom", "GBP", IBAN_DE_VALID, "IBAN country code must match United Kingdom (GB)."),
        ("United States", "USD", "US12 3456 7890", "United States does not use IBANs — enter the account number."),
        ("United States", "USD", "123", "Enter an IBAN or an account number of 4–20 digits."),
        ("United States", "USD", "1" * 21, "Enter an IBAN or an account number of 4–20 digits."),
    ], ids=["bad-checksum", "wrong-length", "other-country-iban", "iban-where-none-used", "3-digits", "21-digits"])
    def test_invalid_account_number(self, bank_page, api_user1, country, currency, identifier, message):
        _expect_rejected(bank_page, api_user1, BANK_HOLDER, BANK_NAME, country, currency, identifier, message)

    # A holder name or bank name that breaks the site's rules is rejected.
    @pytest.mark.parametrize(("holder", "bank", "message"), [
        ("", BANK_NAME, "Account holder name must be 2–100 characters."),
        ("Q", BANK_NAME, "Account holder name must be 2–100 characters."),
        ("QA Tester 2", BANK_NAME, "Account holder name may only contain letters, spaces, and . ' -"),
        (BANK_HOLDER, "<QA Bank>", "Bank name contains invalid characters."),
    ], ids=["empty-holder", "1-char-holder", "digits-in-holder", "html-in-bank-name"])
    def test_invalid_names(self, bank_page, api_user1, holder, bank, message):
        _expect_rejected(bank_page, api_user1, holder, bank, "United States", "USD", US_ACCOUNT_NUMBER, message)

    # With 10 accounts stored (created through the API), an 11th is rejected.
    def test_eleventh_account(self, bank_page, api_user1):
        for i in range(10 - len(api_user1.bank_accounts())):
            api_user1.add_bank_account(BANK_HOLDER, BANK_NAME, "US", "USD", f"1000{i:04d}")
        bank_page.open()

        _expect_rejected(bank_page, api_user1, BANK_HOLDER, BANK_NAME, "United States", "USD", US_ACCOUNT_NUMBER,
                         "You can add up to 10 bank accounts. Remove one to add another.")
