import re

from playwright.sync_api import Locator, Page, expect

NAV_ITEMS = ["Dashboard", "Wallets", "Send Money", "Transaction History",
             "Payment Cards", "Bank Accounts", "Notifications", "Profile & Settings"]


class BasePage:
    """Common behaviour: navigation, headings, toasts, sign-out."""

    path = "/"
    title = ""

    def __init__(self, page: Page):
        self.page = page

    def open(self):
        self.page.goto(self.path)
        return self

    @property
    def heading(self) -> Locator:
        return self.page.get_by_role("heading", name=self.title, exact=True)

    @property
    def sidebar(self) -> Locator:
        return self.page.get_by_role("navigation", name="Main")

    def nav_link(self, label: str) -> Locator:
        return self.sidebar.get_by_role("link", name=label)

    def go_to(self, label: str):
        self.nav_link(label).first.click()

    def text(self, message: str | re.Pattern) -> Locator:
        return self.page.get_by_text(message)

    def toast(self, message: str) -> Locator:
        return self.page.get_by_text(message)

    def sign_out(self):
        self.page.get_by_role("button", name="Account menu").first.click()
        self.page.get_by_role("menuitem", name="Sign out").click()

    def expect_loaded(self):
        expect(self.heading).to_be_visible()
