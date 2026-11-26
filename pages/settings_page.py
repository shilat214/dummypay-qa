
from playwright.sync_api import Locator
from pages.base_page import BasePage


class SettingsPage(BasePage):
    path = "/settings"
    title = "Profile & Settings"

    @property
    def profile(self) -> Locator:
        return self.page.locator("dl").first

    @property
    def display_name_input(self) -> Locator:
        return self.page.get_by_role("textbox", name="Display name")

    @property
    def save_button(self) -> Locator:
        return self.page.get_by_role("button", name="Save")

    @property
    def currency_select(self) -> Locator:
        return self.page.get_by_label("Currency", exact=True)

    @property
    def change_button(self) -> Locator:
        return self.page.get_by_role("button", name="Change")

    @property
    def confirm_dialog(self) -> Locator:
        return self.page.get_by_role("alertdialog")

    def rename(self, name: str):
        self.display_name_input.fill(name)
        self.save_button.click()
        return self

    def current_currency(self):
        return self.currency_select.inner_text().split()[0]

    def different_currency(self):
        return "USD" if self.current_currency() != "USD" else "ILS"

    def change_currency(self, currency):
        self.currency_select.click()
        self.page.get_by_role("option", name=currency).click()
        self.change_button.click()

    def rename(self, name):
        self.display_name_input.fill(name)
        self.save_button.click()
