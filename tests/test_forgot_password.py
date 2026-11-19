import pytest
from playwright.sync_api import expect

from pages.reset_password_page import ResetPasswordPage
from utilities import config
from utilities.data import unknown_email

pytestmark = pytest.mark.regression


class TestForgotPasswordPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_page_shows_email_field_and_send_button(self, forgot_password_page):
        forgot_password_page.open().expect_loaded()
        expect(forgot_password_page.email).to_be_visible()

    def test_valid_email_shows_confirmation_and_calls_recover(self, forgot_password_page):
        email = config.USER1_EMAIL or "someone@test.dummypay.dev"
        tracker = forgot_password_page.mock_recover_endpoint()
        forgot_password_page.open().request_reset(email)
        expect(forgot_password_page.confirmation).to_contain_text(f"If an account exists for {email}")
        assert tracker["called"], "the reset request should reach the auth endpoint"

    def test_unregistered_email_gets_the_same_confirmation(self, forgot_password_page):
        email = unknown_email()
        forgot_password_page.mock_recover_endpoint()
        forgot_password_page.open().request_reset(email)
        # Must not reveal whether the account exists.
        expect(forgot_password_page.confirmation).to_contain_text(f"If an account exists for {email}")


class TestForgotPasswordNegative:
    pytestmark = pytest.mark.negative

    def test_malformed_email_is_rejected(self, forgot_password_page):
        forgot_password_page.open().request_reset("not-an-email")
        expect(forgot_password_page.text("Enter a valid email address.")).to_be_visible()
        expect(forgot_password_page.confirmation).to_have_count(0)

    def test_empty_email_is_rejected(self, forgot_password_page):
        forgot_password_page.open().send_button.click()
        expect(forgot_password_page.text("Enter a valid email address.")).to_be_visible()

    def test_reset_page_without_a_valid_link_explains_what_to_do(self, page):
        reset = ResetPasswordPage(page).open()
        expect(reset.invalid_link_message).to_be_visible()
        expect(reset.request_new_link).to_have_attribute("href", "/forgot-password")
