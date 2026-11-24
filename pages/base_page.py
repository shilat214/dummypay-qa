import re

from playwright.sync_api import Locator, Page, expect

NAV_ITEMS = ["Dashboard", "Wallets", "Send Money", "Transaction History",
             "Payment Cards", "Bank Accounts", "Notifications", "Profile & Settings"]


# Behaviour shared by every page: opening it, its heading, the sidebar, messages and sign-out.
class BasePage:
    path = "/"
    title = ""

    # Keeps the browser tab the page object works on.
    def __init__(self, page: Page):
        self.page = page

    # Opens the page by its path.
    def open(self):
        self.page.goto(self.path)
        return self

    # The page heading (its title).
    @property
    def heading(self) -> Locator:
        return self.page.get_by_role("heading", name=self.title, exact=True)

    # The main navigation sidebar.
    @property
    def sidebar(self) -> Locator:
        return self.page.get_by_role("navigation", name="Main")

    # A link in the sidebar.
    def nav_link(self, label: str) -> Locator:
        return self.sidebar.get_by_role("link", name=label)

    # Any text on the page.
    def text(self, message: str | re.Pattern) -> Locator:
        return self.page.get_by_text(message)

    # A message (toast) shown on the page.
    def toast(self, message: str) -> Locator:
        return self.page.get_by_text(message)

    # Signs out through the account menu (pressing Enter works even when the menu opens near the screen edge).
    def sign_out(self):
        self.page.get_by_role("button", name="Account menu").first.click()
        sign_out = self.page.get_by_role("menuitem", name="Sign out")
        expect(sign_out).to_be_visible()
        sign_out.press("Enter")

    # Checks that the page has loaded (its heading is visible).
    def expect_loaded(self):
        expect(self.heading).to_be_visible()
