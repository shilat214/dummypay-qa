import re

from playwright.sync_api import Locator

from pages.base_page import BasePage


class BankAccountsPage(BasePage):
    path = "/bank-accounts"
    title = "Bank Accounts"

    @property
    def dialog(self) -> Locator:
        return self.page.get_by_role("dialog")

    @property
    def items(self) -> Locator:
        return self.page.get_by_test_id("bank-account-item")

    def open_add_dialog(self):
        self.page.get_by_role("button", name="Add bank account").click()
        return self

    def fill_account(self, holder: str, bank: str, country: str, currency: str, identifier: str):
        self.dialog.get_by_label("Account holder name").fill(holder)
        self.dialog.get_by_label("Bank name").fill(bank)
        self.dialog.get_by_label("Country").click()
        self.page.get_by_role("option", name=country).click()
        self.dialog.get_by_label("Currency").click()
        self.page.get_by_role("option", name=currency).click()
        self.dialog.get_by_label("IBAN or account number").fill(identifier)
        return self

    def submit(self):
        self.dialog.get_by_role("button", name="Add bank account").click()
        return self

    def add_account(self, holder: str, bank: str, country: str, currency: str, identifier: str):
        self.open_add_dialog()
        self.fill_account(holder, bank, country, currency, identifier)
        return self.submit()

    def item_by_bank(self, bank: str) -> Locator:
        return self.items.filter(has_text=bank)

    def item_for(self, bank: str, masked: str) -> Locator:
        """The card of one specific account (bank name + masked number)."""
        return self.item_by_bank(bank).filter(has_text=masked)

    def error(self, message: str) -> Locator:
        """A validation or form error shown inside the add dialog."""
        return self.dialog.get_by_text(message)

    def remove_account(self, bank: str):
        item = self.item_by_bank(bank).first
        item.get_by_role("button", name=re.compile(f"Remove {re.escape(bank)} account")).click()
        self.page.get_by_role("alertdialog").get_by_role("button", name="Remove").click()
