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
    def confirm_add_button(self) -> Locator:
        """The 'Add wallet' button inside the dialog (not the one on the page)."""
        return self.dialog.get_by_role("button", name="Add wallet", exact=True)

    @property
    def wallet_cards(self) -> Locator:
        return self.page.locator('[data-testid^="wallet-"]')

    def wallet_card(self, currency: str) -> Locator:
        return self.page.get_by_test_id(f"wallet-{currency}")

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

    def choose_first_missing_currency(self) -> str:
        """Open the currency list, pick the first option and return its code (e.g. 'USD')."""
        self.dialog.get_by_label("Currency").click()
        option = self.currency_options().first
        code = re.search(r"[A-Z]{3}", option.inner_text()).group(0)
        option.click()
        return code


    def set_preview_amount(self, amount: str):
        self.preview_amount.fill(amount)
