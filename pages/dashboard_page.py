import re

from playwright.sync_api import Locator

from pages.base_page import BasePage


class DashboardPage(BasePage):
    path = "/"
    title = "Dashboard"

    @property
    def welcome(self) -> Locator:
        return self.page.get_by_text(re.compile(r"Welcome back"))

    @property
    def total_balance(self) -> Locator:
        return self.page.get_by_test_id("total-balance")

    @property
    def wallet_cards(self) -> Locator:
        return self.page.locator('[data-testid^="wallet-"]')

    @property
    def rates_card(self) -> Locator:
        return self.page.get_by_test_id("rates-card")

    @property
    def recent_transactions(self) -> Locator:
        return self.page.get_by_test_id("recent-transactions")

    @property
    def recent_notifications(self) -> Locator:
        return self.page.get_by_test_id("recent-notifications")
