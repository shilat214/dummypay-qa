
import re
from playwright.sync_api import Locator, expect
from pages.base_page import BasePage

class HistoryPage(BasePage):
    path = "/history"
    title = "Transaction History"

    @property
    def rows(self) -> Locator:
        return self.page.get_by_role("main").get_by_role("listitem")

    @property
    def detail(self) -> Locator:
        return self.page.get_by_test_id("transaction-detail")

    @property
    def from_date(self) -> Locator:
        return self.page.get_by_label("From date")

    @property
    def to_date(self) -> Locator:
        return self.page.get_by_label("To date")

    @property
    def type_filter(self) -> Locator:
        return self.page.get_by_label("Type")

    @property
    def currency_filter(self) -> Locator:
        return self.page.get_by_label("Currency")

    @property
    def clear_button(self) -> Locator:
        return self.page.get_by_role("button", name="Clear")

    @property
    def no_match(self) -> Locator:
        return self.page.get_by_text("No matching transactions", exact=True)

    @property
    def transaction_count(self) -> Locator:
        return self.page.get_by_text(re.compile(r"^\d+ transactions?$"))

    @property
    def next_button(self) -> Locator:
        return self.page.get_by_role("button", name="Next")

    def choose_type(self, label: str):
        self.type_filter.click()
        self.page.get_by_role("option", name=label, exact=True).click()
        expect(self.rows.first.filter(has_text=label).or_(self.no_match)).to_be_visible()
        return self

    def choose_currency(self, currency: str):
        self.currency_filter.click()
        self.page.get_by_role("option", name=currency, exact=True).click()
        return self

    def count_all_transactions(self):
        total = int(self.transaction_count.inner_text().split()[0])
        counted = 0
        while True:
            expect(self.rows).to_have_count(min(20, total - counted))
            counted += self.rows.count()
            if self.next_button.is_disabled():
                break
            self.next_button.click()
        return counted

    def open_first_transaction(self):
        row = self.rows.first
        amount = row.locator("span").last.inner_text()
        row.click()
        return amount.lstrip("−-")
