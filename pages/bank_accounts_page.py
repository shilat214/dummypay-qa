from playwright.sync_api import Locator

from pages.base_page import BasePage


class BankAccountsPage(BasePage):
    path = "/bank-accounts"
    title = "Bank Accounts"

    # The "Add a simulated bank account" dialog.
    @property
    def dialog(self) -> Locator:
        return self.page.get_by_role("dialog")

    # All bank account cards on the page.
    @property
    def items(self) -> Locator:
        return self.page.get_by_test_id("bank-account-item")

    # Opens the add-account dialog.
    def open_add_dialog(self):
        self.page.get_by_role("button", name="Add bank account").click()

    # The "Account holder name" field of the add dialog.
    @property
    def holder_input(self) -> Locator:
        return self.dialog.get_by_label("Account holder name")

    # Fills every field of the add-account dialog.
    def fill_account(self, holder: str, bank: str, country: str, currency: str, identifier: str):
        self.holder_input.fill(holder)
        self.dialog.get_by_label("Bank name").fill(bank)
        self.dialog.get_by_label("Country").click()
        self.page.get_by_role("option", name=country).click()
        self.dialog.get_by_label("Currency").click()
        self.page.get_by_role("option", name=currency).click()
        self.dialog.get_by_label("IBAN or account number").fill(identifier)

    # Clicks the dialog's "Add bank account" button.
    def submit(self):
        self.dialog.get_by_role("button", name="Add bank account").click()

    # Closes the add-account dialog with one of its buttons ("Cancel" or the "Close" X).
    def close_dialog(self, button: str):
        self.dialog.get_by_role("button", name=button, exact=True).click()

    # Opens the dialog, fills it and submits it.
    def add_account(self, holder: str, bank: str, country: str, currency: str, identifier: str):
        self.open_add_dialog()
        self.fill_account(holder, bank, country, currency, identifier)
        self.submit()

    # The cards of all accounts with this bank name.
    def item_by_bank(self, bank: str) -> Locator:
        return self.items.filter(has_text=bank)

    # The card of one account (bank name + masked number).
    def item_for(self, bank: str, masked: str) -> Locator:
        return self.item_by_bank(bank).filter(has_text=masked)

    # An error message shown inside the add dialog.
    def error(self, message: str) -> Locator:
        return self.dialog.get_by_text(message)

    # Removes the first account with this bank name and confirms.
    def remove_account(self, bank: str):
        item = self.item_by_bank(bank).first
        item.get_by_role("button", name=f"Remove {bank} account").click()
        self.page.get_by_role("alertdialog").get_by_role("button", name="Remove").click()
