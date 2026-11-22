import re

import pytest
from playwright.sync_api import expect

from pages.history_page import HistoryPage
from utilities.data import unknown_email
from utilities.flows import send_money

pytestmark = pytest.mark.regression


class TestSendMoneyPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_registered_recipient_is_found_and_confirmed(self, send_page, user2_email):
        send_page.expect_loaded()
        send_page.find_recipient(user2_email)
        expect(send_page.recipient_card).to_contain_text(user2_email)

    def test_recipient_lookup_ignores_email_case(self, send_page, user2_email):
        send_page.find_recipient(user2_email.upper())
        expect(send_page.recipient_card).to_contain_text(user2_email)

    def test_review_step_shows_amount_rate_and_recipient(self, send_page, user2_email):
        send_page.find_recipient(user2_email).continue_to_amount()
        send_page.enter_amount_and_review("1")
        expect(send_page.summary).to_be_visible()
        expect(send_page.summary_send).to_contain_text(re.compile(r"[\d,]+\.\d{2}"))
        expect(send_page.summary_receive).to_contain_text(re.compile(r"[\d,]+\.\d{2}"))
        # Same currency for both users -> no conversion; otherwise "1 XXX = n XXX".
        expect(send_page.summary_rate).to_have_text(
            re.compile(r"No conversion \(same currency\)|1 [A-Z]{3} = [\d.]+ [A-Z]{3}"))

    def test_cancelling_the_confirmation_does_not_send_money(self, send_page, user2_email):
        send_page.find_recipient(user2_email).continue_to_amount()
        send_page.enter_amount_and_review("1")
        send_page.cancel_confirmation()
        expect(send_page.success).to_have_count(0)
        expect(send_page.summary).to_be_visible()

    @pytest.mark.nightly
    def test_full_transfer_moves_money_and_appears_in_history(self, user1_page, api_user1, api_user2, user2_email):
        """End to end: balances of both users change by the quoted amounts, and the new
        transaction is the newest one in the history (checked by its ID, not by row count,
        because the history page shows only 20 rows per page)."""
        last_before = api_user1.latest_transaction()
        sender_before, recipient_before = api_user1.wallets(), api_user2.wallets()

        send_money(user1_page, user2_email, "1")

        txn = api_user1.latest_transaction()
        assert txn["id"] != (last_before or {}).get("id"), "a new transaction must be recorded"
        assert txn["direction"] == "sent" and txn["recipient_email"] == user2_email
        assert txn["sending_amount_minor"] == 100  # "1" in the sender's currency

        send_ccy, recv_ccy = txn["sending_currency"], txn["receiving_currency"]
        assert api_user1.wallets()[send_ccy] == sender_before[send_ccy] - txn["sending_amount_minor"]
        assert api_user2.wallets()[recv_ccy] == recipient_before.get(recv_ccy, 0) + txn["receiving_amount_minor"]

        history = HistoryPage(user1_page).open()
        history.rows.first.click()
        expect(history.detail).to_contain_text(txn["id"])


class TestSendMoneyNegative:
    pytestmark = pytest.mark.negative

    def test_unregistered_recipient_is_rejected(self, send_page):
        send_page.find_recipient(unknown_email())
        expect(send_page.text("No registered user found with this email address.")).to_be_visible()
        expect(send_page.recipient_card).to_have_count(0)

    def test_sending_to_yourself_is_rejected(self, send_page, user1_email):
        send_page.find_recipient(user1_email)
        expect(send_page.text("You cannot send money to yourself.")).to_be_visible()

    def test_malformed_recipient_email_is_rejected(self, send_page):
        send_page.find_recipient("not-an-email")
        expect(send_page.text("Enter a valid email address.")).to_be_visible()

    def test_zero_amount_is_rejected(self, send_page, user2_email):
        send_page.find_recipient(user2_email).continue_to_amount()
        send_page.enter_amount_and_review("0")
        expect(send_page.text("Amount must be greater than zero.")).to_be_visible()

    def test_amount_above_balance_is_rejected(self, send_page, user2_email):
        send_page.find_recipient(user2_email).continue_to_amount()
        send_page.enter_amount_and_review("999999")
        expect(send_page.text(re.compile(r"You only have .+ available\."))).to_be_visible()
