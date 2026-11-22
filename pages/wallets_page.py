import re

from playwright.sync_api import Locator, expect

from pages.base_page import BasePage
from utilities.money import format_minor, to_minor

CURRENCY_CODE = re.compile(r"\b(ILS|USD|EUR|GBP)\b")


class WalletsPage(BasePage):
    path = "/wallets"
    title = "Wallets"

    # ---- header / add-wallet dialog --------------------------------------------
    @property
    def add_wallet_button(self) -> Locator:
        return self.page.get_by_role("button", name="Add wallet")

    @property
    def dialog(self) -> Locator:
        return self.page.get_by_role("dialog")

    @property
    def dialog_currency(self) -> Locator:
        return self.dialog.get_by_label("Currency")

    @property
    def confirm_add_button(self) -> Locator:
        """The 'Add wallet' button inside the dialog (not the one on the page)."""
        return self.dialog.get_by_role("button", name="Add wallet", exact=True)

    def currency_options(self) -> Locator:
        return self.page.get_by_role("option")

    def offered_currencies(self) -> list[str]:
        """Open the dialog's currency list and return the codes it offers."""
        self.add_wallet_button.click()
        self.dialog_currency.click()
        self.currency_options().first.wait_for()
        codes = [CURRENCY_CODE.search(t).group(1) for t in self.currency_options().all_inner_texts()]
        self.page.keyboard.press("Escape")  # close the list
        self.page.keyboard.press("Escape")  # close the dialog
        expect(self.dialog).to_be_hidden()
        return codes

    def add_wallet(self, currency: str):
        """Full UI flow: open dialog, choose currency, confirm, wait for the new card."""
        self.add_wallet_button.click()
        self.dialog_currency.click()
        self.currency_options().filter(has_text=currency).click()
        self.confirm_add_button.click()
        expect(self.dialog).to_be_hidden()
        expect(self.wallet_card(currency)).to_be_visible()
        return self

    # ---- wallet cards / total ----------------------------------------------------
    @property
    def wallet_cards(self) -> Locator:
        return self.page.locator('[data-testid^="wallet-"]')

    def wallet_card(self, currency: str) -> Locator:
        return self.page.get_by_test_id(f"wallet-{currency}")

    def owned_wallets_count(self) -> int:
        self.wallet_cards.first.wait_for()
        return self.wallet_cards.count()

    def shown_currencies(self) -> set[str]:
        self.wallet_cards.first.wait_for()
        ids = [c.get_attribute("data-testid") for c in self.wallet_cards.all()]
        return {i.removeprefix("wallet-") for i in ids}

    def balance_minor(self, currency: str) -> int:
        """Balance shown on a wallet card, in minor units (₪13,000.00 -> 1300000)."""
        return to_minor(self.wallet_card(currency).inner_text())

    @property
    def total_balance(self) -> Locator:
        return self.page.get_by_test_id("total-balance")

    def total_minor(self) -> int:
        expect(self.total_balance).to_contain_text(re.compile(r"\d\.\d{2}"))  # skeleton gone
        return to_minor(self.total_balance.inner_text())

    # ---- exchange rates card -----------------------------------------------------
    @property
    def rates_card(self) -> Locator:
        return self.page.get_by_test_id("rates-card")

    def shown_rates(self) -> dict[str, float]:
        """{to_currency: rate} as displayed, e.g. 'rate-ILS-USD' -> {'USD': 0.2739}."""
        rows = self.rates_card.locator('[data-testid^="rate-"]')
        rows.first.wait_for()
        rates = {}
        for row in rows.all():
            to = row.get_attribute("data-testid").rsplit("-", 1)[1]
            rates[to] = float(row.inner_text().replace(",", ""))
        return rates

    # ---- conversion preview ------------------------------------------------------
    @property
    def preview(self) -> Locator:
        return self.page.get_by_test_id("conversion-preview")

    @property
    def preview_amount(self) -> Locator:
        return self.preview.get_by_label("Amount")

    @property
    def preview_result(self) -> Locator:
        return self.preview.get_by_test_id("conversion-result")

    @property
    def preview_server_error(self) -> Locator:
        return self.preview.get_by_role("alert")

    @property
    def swap_button(self) -> Locator:
        return self.preview.get_by_role("button", name="Swap")

    def preview_currencies(self) -> tuple[str, str]:
        """(from, to) currently selected in the preview."""
        frm = self.preview.get_by_label("From").inner_text()
        to = self.preview.get_by_label("To").inner_text()
        return CURRENCY_CODE.search(frm).group(1), CURRENCY_CODE.search(to).group(1)

    def set_preview_amount(self, amount: str):
        self.preview_amount.fill(amount)
        return self

    def expect_preview_result(self, minor: int):
        """Retry until the (debounced, server-computed) result shows exactly `minor`."""
        exact = re.compile(rf"(?<![\d,]){re.escape(format_minor(minor))}$")
        expect(self.preview_result).to_have_text(exact)

    def expect_no_preview_result(self):
        expect(self.preview_result).to_have_text("—")
