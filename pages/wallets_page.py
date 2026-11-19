import re

from playwright.sync_api import Locator

from pages.base_page import BasePage


class WalletsPage(BasePage):
    path = "/wallets"
    title = "Wallets"

    @property
    def add_wallet_button(self) -> Locator:
        return self.page.get_by_role("button", name="Add wallet")

    @property
    def dialog(self) -> Locator:
        return self.page.get_by_role("dialog")

    @property
    def wallet_cards(self) -> Locator:
        return self.page.locator('[data-testid^="wallet-"]')

    @property
    def total_balance(self) -> Locator:
        return self.page.get_by_test_id("total-balance")

    @property
    def preview(self) -> Locator:
        return self.page.get_by_test_id("conversion-preview")

    @property
    def preview_amount(self) -> Locator:
        return self.preview.get_by_label("Amount")

    @property
    def preview_result(self) -> Locator:
        return self.preview.get_by_test_id("conversion-result")

    def owned_wallets_count(self) -> int:
        self.wallet_cards.first.wait_for()
        return self.wallet_cards.count()
    
    def open_add_wallet_dialog(self):
        self.add_wallet_button.click()
        self.dialog.get_by_label("Currency").click()
        return self

    def currency_options(self) -> Locator:
        return self.page.get_by_role("option")

    def add_wallet(self, currency: str):
        self.dialog.get_by_label("Currency").click()
        self.page.get_by_role("option", name=re.compile(currency)).click()
        self.dialog.get_by_role("button", name="Add wallet").click()

    def set_preview_amount(self, amount: str):
        self.preview_amount.fill(amount)
