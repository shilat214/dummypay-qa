"""Bank Accounts page - 3 positive, 3 negative.

The UI is what we test. The API is used only where it is simpler than the UI:
  * to read what the server really stored (expected values),
  * to create test accounts (setup) and delete them (cleanup, in the bank_page fixture).
Browser and server validate with the same rules, so every negative case is checked
in both places: the form shows the error, and the server rejects the same data too.
"""
import pytest
from playwright.sync_api import expect

from utilities.api_client import ApiError
from utilities.data import (BANK_HOLDER, BANK_NAME, DE_ACCOUNT, IBAN_DE_VALID,
                            IBAN_GB_BAD_CHECKSUM, IBAN_GB_TOO_SHORT,
                            UK_ACCOUNT, US_ACCOUNT, US_ACCOUNT_NUMBER)

pytestmark = pytest.mark.regression

MAX_ACCOUNTS = 10  # per user, enforced by the server


def _shown_identifier(account: dict) -> str:
    """How the page prints a stored account number, e.g. 'IBAN GB•• •••• 5432'."""
    prefix = "IBAN" if account["identifier_type"] == "iban" else "Account"
    return f"{prefix} {account['masked_account_identifier']}"


def _test_accounts(api) -> list[dict]:
    return [a for a in api.bank_accounts() if a["bank_name"] == BANK_NAME]


@pytest.fixture
def existing_account(bank_page, api_user1) -> dict:
    """A test account created through the API (setup), already shown on the open page.
    It is deleted after the test by the bank_page fixture, like every test account."""
    account = api_user1.add_bank_account(BANK_HOLDER, BANK_NAME, "US", "USD", US_ACCOUNT_NUMBER)
    bank_page.open()  # reload, so the page shows the new account
    return account


class TestBankAccountsPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_page_lists_exactly_the_server_accounts(self, bank_page, api_user1, existing_account):
        server = api_user1.bank_accounts()

        expect(bank_page.items).to_have_count(len(server))
        for account in server:
            item = bank_page.item_for(account["bank_name"], account["masked_account_identifier"])
            expect(item.first).to_contain_text(_shown_identifier(account))
            expect(item.first).to_contain_text(f"{account['account_holder_name']} · ")
            expect(item.first).to_contain_text(account["currency"])

    @pytest.mark.parametrize("account", [
        pytest.param(UK_ACCOUNT, id="uk-iban", marks=pytest.mark.smoke),
        pytest.param(DE_ACCOUNT, id="germany-iban"),
        pytest.param(US_ACCOUNT, id="us-account-number"),
    ])
    def test_added_account_is_shown_and_stored_masked_only(self, bank_page, api_user1, account):
        bank_page.add_account(BANK_HOLDER, BANK_NAME, account["country"], account["currency"], account["identifier"])
        expect(bank_page.dialog).to_be_hidden(timeout=20_000)  # server may be slow (cold start)
        expect(bank_page.toast("Simulated bank account added.")).to_be_visible()

        # Server: exactly one new account, stored masked - the full number is never saved.
        stored = _test_accounts(api_user1)
        assert len(stored) == 1
        row = stored[0]
        assert (row["country"], row["currency"]) == (account["code"], account["currency"])
        assert row["identifier_type"] == account["type"]
        assert row["masked_account_identifier"] == account["masked"]
        full_number = account["identifier"].replace(" ", "")
        assert full_number not in str(row), "the full account number must not be stored"

        # UI: the card shows the same data as the server.
        item = bank_page.item_for(BANK_NAME, account["masked"])
        expect(item).to_have_count(1)
        expect(item).to_contain_text(_shown_identifier(row))
        expect(item).to_contain_text(f"{BANK_HOLDER} · {account['country']} · {account['currency']}")
        expect(item).to_contain_text("Simulated")

    def test_removed_account_disappears_from_page_and_server(self, bank_page, api_user1, existing_account):
        expect(bank_page.item_by_bank(BANK_NAME)).to_have_count(1)

        bank_page.remove_account(BANK_NAME)

        expect(bank_page.toast("Bank account removed.")).to_be_visible()
        expect(bank_page.item_by_bank(BANK_NAME)).to_have_count(0)
        assert _test_accounts(api_user1) == []


def _expect_rejected_by_form_and_server(bank_page, api, form: dict, field: str, message: str):
    """The form shows `message` and saves nothing; the server rejects the same data with the same message."""
    before = len(api.bank_accounts())

    bank_page.add_account(form["holder"], form["bank"], form["country"], form["currency"], form["identifier"])
    expect(bank_page.error(message)).to_be_visible()
    expect(bank_page.dialog).to_be_visible()  # dialog stays open
    assert len(api.bank_accounts()) == before, "a rejected account must not be stored"

    with pytest.raises(ApiError) as e:
        api.add_bank_account(form["holder"], form["bank"], form["code"], form["currency"], form["identifier"])
    assert e.value.status == 400 and e.value.code == "VALIDATION_FAILED"
    assert e.value.body["fields"][field] == message


def _form(country="United States", code="US", currency="USD", identifier=US_ACCOUNT_NUMBER,
          holder=BANK_HOLDER, bank=BANK_NAME) -> dict:
    return {"country": country, "code": code, "currency": currency,
            "identifier": identifier, "holder": holder, "bank": bank}


UK = {"country": "United Kingdom", "code": "GB", "currency": "GBP"}


class TestBankAccountsNegative:
    pytestmark = pytest.mark.negative

    @pytest.mark.parametrize(("form", "message"), [
        (_form(**UK, identifier=IBAN_GB_BAD_CHECKSUM), "IBAN is not valid (checksum failed)."),
        (_form(**UK, identifier=IBAN_GB_TOO_SHORT), "A United Kingdom IBAN has 22 characters."),
        (_form(**UK, identifier=IBAN_DE_VALID), "IBAN country code must match United Kingdom (GB)."),
        (_form(identifier="US12 3456 7890"), "United States does not use IBANs — enter the account number."),
        (_form(identifier="123"), "Enter an IBAN or an account number of 4–20 digits."),
        (_form(identifier="1" * 21), "Enter an IBAN or an account number of 4–20 digits."),
    ], ids=["bad-checksum", "wrong-length", "other-country-iban", "iban-where-none-used",
            "3-digits", "21-digits"])
    def test_invalid_account_number_is_rejected(self, bank_page, api_user1, form, message):
        _expect_rejected_by_form_and_server(bank_page, api_user1, form, "accountIdentifier", message)

    @pytest.mark.parametrize(("form", "field", "message"), [
        (_form(holder=""), "accountHolderName", "Account holder name must be 2–100 characters."),
        (_form(holder="Q"), "accountHolderName", "Account holder name must be 2–100 characters."),
        (_form(holder="QA Tester 2"), "accountHolderName",
         "Account holder name may only contain letters, spaces, and . ' -"),
        (_form(bank="<QA Bank>"), "bankName", "Bank name contains invalid characters."),
    ], ids=["empty-holder", "1-char-holder", "digits-in-holder", "html-in-bank-name"])
    def test_invalid_names_are_rejected(self, bank_page, api_user1, form, field, message):
        _expect_rejected_by_form_and_server(bank_page, api_user1, form, field, message)

    def test_eleventh_account_is_rejected(self, bank_page, api_user1):
        """Boundary: a user may store at most 10 accounts. Filling up to 10 goes through
        the API (setup); the 11th is tried in the UI. The fixture deletes the test accounts."""
        for i in range(MAX_ACCOUNTS - len(api_user1.bank_accounts())):
            api_user1.add_bank_account(BANK_HOLDER, BANK_NAME, "US", "USD", f"1000{i:04d}")
        bank_page.open()
        expect(bank_page.items).to_have_count(MAX_ACCOUNTS)

        bank_page.add_account(BANK_HOLDER, BANK_NAME, "United States", "USD", US_ACCOUNT_NUMBER)

        expect(bank_page.error("You can add up to 10 bank accounts. Remove one to add another.")).to_be_visible()
        assert len(api_user1.bank_accounts()) == MAX_ACCOUNTS
