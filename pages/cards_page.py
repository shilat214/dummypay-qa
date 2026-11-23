import re

from playwright.sync_api import Locator

from pages.base_page import BasePage


class CardsPage(BasePage):
    path = "/cards"
    title = "Payment Cards"

    # The "Add a simulated card" dialog.
    @property
    def dialog(self) -> Locator:
        return self.page.get_by_role("dialog")

    # All card tiles on the page.
    @property
    def items(self) -> Locator:
        return self.page.get_by_test_id("card-item")

    # Opens the add-card dialog.
    def open_add_dialog(self):
        self.page.get_by_role("button", name="Add card").click()
        return self

    # The card number field of the add-card dialog.
    @property
    def card_number_input(self) -> Locator:
        return self.dialog.get_by_label("Card number")

    # Fills every field of the add-card dialog.
    def fill_card(self, name: str, number: str, expiry: str, cvv: str):
        self.dialog.get_by_label("Cardholder name").fill(name)
        self.card_number_input.fill(number)
        self.dialog.get_by_label("Expiry (MM/YY)").fill(expiry)
        self.dialog.get_by_label("CVV").fill(cvv)
        return self

    # Clicks the dialog's "Add card" button.
    def submit(self):
        self.dialog.get_by_role("button", name="Add card").click()
        return self

    # Opens the dialog, fills it and submits it.
    def add_card(self, name: str, number: str, expiry: str, cvv: str):
        self.open_add_dialog()
        self.fill_card(name, number, expiry, cvv)
        return self.submit()

    # The tiles of all cards ending in these four digits.
    def item_by_last4(self, last4: str) -> Locator:
        return self.items.filter(has_text=last4)

    # An error message shown inside the add dialog.
    def error(self, message: str) -> Locator:
        return self.dialog.get_by_text(message)

    # Removes the first card ending in these four digits and confirms.
    def remove_card(self, last4: str):
        item = self.item_by_last4(last4).first
        item.get_by_role("button", name=re.compile(f"Remove card ending in {last4}")).click()
        self.page.get_by_role("alertdialog").get_by_role("button", name="Remove").click()
