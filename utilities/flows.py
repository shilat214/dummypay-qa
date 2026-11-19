"""Reusable multi-step business flows built on top of the page objects."""
from playwright.sync_api import Page, expect

from pages.send_money_page import SendMoneyPage


def send_money(page: Page, recipient_email: str, amount: str = "1") -> SendMoneyPage:
    """Send `amount` (in the sender's currency) to a registered user and wait for success."""
    send = SendMoneyPage(page).open()
    send.find_recipient(recipient_email)
    expect(send.recipient_card).to_be_visible()
    send.continue_to_amount()
    send.enter_amount_and_review(amount)
    send.confirm_and_send()
    expect(send.success).to_contain_text("Transfer complete")
    return send
