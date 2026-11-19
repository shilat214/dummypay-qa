import re

from playwright.sync_api import Locator

from pages.base_page import BasePage


class SendMoneyPage(BasePage):
    path = "/send"
    title = "Send Money"

    @property
    def recipient_email(self) -> Locator:
        return self.page.get_by_label("Recipient's email")

    @property
    def find_button(self) -> Locator:
        return self.page.get_by_role("button", name="Find recipient")

    @property
    def recipient_card(self) -> Locator:
        return self.page.get_by_test_id("recipient-card")

    @property
    def amount_input(self) -> Locator:
        return self.page.get_by_label(re.compile(r"Amount (to send|they receive) \([A-Z]{3}\)"))

    @property
    def review_button(self) -> Locator:
        return self.page.get_by_role("button", name="Review transfer")

    @property
    def confirm_button(self) -> Locator:
        return self.page.get_by_role("button", name="Confirm & send")

    @property
    def confirm_dialog(self) -> Locator:
        return self.page.get_by_role("alertdialog")

    @property
    def summary(self) -> Locator:
        return self.page.get_by_test_id("transfer-summary")

    @property
    def summary_send(self) -> Locator:
        return self.page.get_by_test_id("summary-send")

    @property
    def summary_receive(self) -> Locator:
        return self.page.get_by_test_id("summary-receive")

    @property
    def summary_rate(self) -> Locator:
        return self.page.get_by_test_id("summary-rate")

    @property
    def success(self) -> Locator:
        return self.page.get_by_test_id("transfer-success")

    def find_recipient(self, email: str):
        self.recipient_email.fill(email)
        self.find_button.click()
        return self

    def continue_to_amount(self):
        self.recipient_card.get_by_role("button", name="Continue").click()
        return self

    def enter_amount_and_review(self, amount: str):
        self.amount_input.fill(amount)
        self.review_button.click()
        return self

    def confirm_and_send(self):
        self.confirm_button.click()
        self.confirm_dialog.get_by_role("button", name="Send now").click()
        return self

    def cancel_confirmation(self):
        self.confirm_button.click()
        self.confirm_dialog.get_by_role("button", name="Cancel").click()
        return self
