import re

from playwright.sync_api import Locator, expect

from pages.base_page import BasePage
from utilities.money import format_minor, to_minor

CURRENCY_CODE = re.compile(r"\b(ILS|USD|EUR|GBP)\b")


class WalletsPage(BasePage):
    path = "/wallets"
    title = "Wallets"

    # The "Add wallet" button at the top of the page.
    @property
    def add_wallet_button(self) -> Locator:
        return self.page.get_by_role("button", name="Add wallet")

    # All wallet cards (one per currency).
    @property
    def wallet_cards(self) -> Locator:
        return self.page.locator('[data-testid^="wallet-"]')

    # The card of one currency's wallet.
    def wallet_card(self, currency: str) -> Locator:
        return self.page.get_by_test_id(f"wallet-{currency}")

    # The currencies of the wallet cards shown on the page.
    def shown_currencies(self) -> set[str]:
        self.wallet_cards.first.wait_for()
        ids = [c.get_attribute("data-testid") for c in self.wallet_cards.all()]
        return {i.removeprefix("wallet-") for i in ids}

    # The balance shown on one wallet card, in minor units (₪13,000.00 -> 1300000).
    def balance_minor(self, currency: str) -> int:
        return to_minor(self.wallet_card(currency).inner_text())

    # The total balance card.
    @property
    def total_balance(self) -> Locator:
        return self.page.get_by_test_id("total-balance")

    # The total balance shown, in minor units (waits until the amount has loaded).
    def total_minor(self) -> int:
        expect(self.total_balance).to_contain_text(re.compile(r"\d\.\d{2}"))
        return to_minor(self.total_balance.inner_text())

    # The exchange rates card.
    @property
    def rates_card(self) -> Locator:
        return self.page.get_by_test_id("rates-card")

    # The rates shown in the rates card, e.g. {"USD": 0.2739, "EUR": 0.2512}.
    def shown_rates(self) -> dict[str, float]:
        rows = self.rates_card.locator('[data-testid^="rate-"]')
        rows.first.wait_for()
        rates = {}
        for row in rows.all():
            to = row.get_attribute("data-testid").rsplit("-", 1)[1]
            rates[to] = float(row.inner_text().replace(",", ""))
        return rates

    # The conversion preview card.
    @property
    def preview(self) -> Locator:
        return self.page.get_by_test_id("conversion-preview")

    # The amount field of the conversion preview.
    @property
    def preview_amount(self) -> Locator:
        return self.preview.get_by_label("Amount")

    # The converted result of the conversion preview.
    @property
    def preview_result(self) -> Locator:
        return self.preview.get_by_test_id("conversion-result")

    # An error message shown in the conversion preview.
    def preview_error(self, message: str) -> Locator:
        return self.preview.get_by_text(message)
    
    # All error messages shown in the conversion preview (from the browser or from the server).
    @property
    def preview_errors(self) -> Locator:
        return self.preview.get_by_role("alert")
    
    # Swaps the "From" and "To" currencies.
    def swap(self):
        self.preview.get_by_role("button", name="Swap").click()

    # The (from, to) currencies selected in the conversion preview.
    def preview_currencies(self) -> tuple[str, str]:
        frm = self.preview.get_by_label("From").inner_text()
        to = self.preview.get_by_label("To").inner_text()
        return CURRENCY_CODE.search(frm).group(1), CURRENCY_CODE.search(to).group(1)

    # Types an amount into the conversion preview.
    def set_preview_amount(self, amount: str):
        self.preview_amount.fill(amount)

    # Waits until the preview shows exactly this result (given in minor units).
    def expect_preview_result(self, minor: int):
        exact = re.compile(rf"(?<![\d,]){re.escape(format_minor(minor))}$")
        expect(self.preview_result).to_have_text(exact)

    # Checks that the preview shows no result ("—").
    def expect_no_preview_result(self):
        expect(self.preview_result).to_have_text("—")

