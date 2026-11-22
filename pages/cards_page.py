import re

from playwright.sync_api import Locator

from pages.base_page import BasePage


class CardsPage(BasePage):
    path = "/cards"
    title = "Payment Cards"

    @property
    def dialog(self) -> Locator:
        return self.page.get_by_role("dialog")

    @property
    def items(self) -> Locator:
        return self.page.get_by_test_id("card-item")

    @property
    def empty_state(self) -> Locator:
        return self.page.get_by_text("No cards yet")

    @property
    def disclaimer(self) -> Locator:
        return self.page.get_by_text(re.compile(r"not been verified by a financial institution"))

    def open_add_dialog(self):
        self.page.get_by_role("button", name="Add card").click()
        return self

    def fill_card(self, name: str, number: str, expiry: str, cvv: str):
        self.dialog.get_by_label("Cardholder name").fill(name)
        self.dialog.get_by_label("Card number").fill(number)
        self.dialog.get_by_label("Expiry (MM/YY)").fill(expiry)
        self.dialog.get_by_label("CVV").fill(cvv)
        return self

    def submit(self):
        self.dialog.get_by_role("button", name="Add card").click()
        return self

    def add_card(self, name: str, number: str, expiry: str, cvv: str):
        self.open_add_dialog()
        self.fill_card(name, number, expiry, cvv)
        return self.submit()

    def item_by_last4(self, last4: str) -> Locator:
        return self.items.filter(has_text=last4)

    def remove_card(self, last4: str):
        item = self.item_by_last4(last4).first
        item.get_by_role("button", name=re.compile(f"Remove card ending in {last4}")).click()
        self.page.get_by_role("alertdialog").get_by_role("button", name="Remove").click()
