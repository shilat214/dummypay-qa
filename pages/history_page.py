from playwright.sync_api import Locator

from pages.base_page import BasePage


class HistoryPage(BasePage):
    path = "/history"
    title = "Transaction History"

    @property
    def rows(self) -> Locator:
        return self.page.get_by_test_id("transaction-row")

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
    def clear_button(self) -> Locator:
        return self.page.get_by_role("button", name="Clear")

    @property
    def no_match(self) -> Locator:
        return self.page.get_by_text("No matching transactions")

    def choose_type(self, label: str):
        self.type_filter.click()
        self.page.get_by_role("option", name=label).click()
        return self
