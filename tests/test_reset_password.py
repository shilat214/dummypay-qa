"""Reset Password page.

The real link arrives by e-mail, so the e-mail step is not automated. A signed-in session also
makes the page show its new-password form, so these tests use user 1's saved session. Every
negative test fails client-side validation: no password is ever changed and nothing is sent.
(The "invalid link" state without a session is covered in test_forgot_password.py.)
"""
import re

import pytest
from playwright.sync_api import expect

from utilities import config

pytestmark = pytest.mark.regression


class TestResetPasswordPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_form_is_shown_for_the_account(self, reset_password_page):
        reset_password_page.expect_loaded()
        expect(reset_password_page.new_password).to_be_visible()
        expect(reset_password_page.confirm_password).to_be_visible()
        expect(reset_password_page.update_button).to_be_enabled()
        if config.USER1_EMAIL:
            expect(reset_password_page.account_note).to_contain_text(config.USER1_EMAIL)

    def test_password_hint_and_masked_fields(self, reset_password_page):
        expect(reset_password_page.password_hint).to_be_visible()
        expect(reset_password_page.new_password).to_have_attribute("type", "password")
        expect(reset_password_page.confirm_password).to_have_attribute("type", "password")

    def test_back_to_sign_in_link_points_to_login(self, reset_password_page):
        expect(reset_password_page.back_to_sign_in).to_have_attribute("href", "/login")


class TestResetPasswordNegative:
    pytestmark = pytest.mark.negative

    def test_empty_form_is_rejected(self, reset_password_page):
        reset_password_page.update_button.click()
        expect(reset_password_page.text("Password must be at least 8 characters.")).to_be_visible()
        expect(reset_password_page.page).to_have_url(re.compile(r"/reset-password$"))

    def test_password_shorter_than_eight_characters_is_rejected(self, reset_password_page):
        reset_password_page.try_password("short", "short")
        expect(reset_password_page.text("Password must be at least 8 characters.")).to_be_visible()

    def test_password_confirmation_must_match(self, reset_password_page):
        reset_password_page.try_password("Valid-Pass-123", "Different-Pass-1")
        expect(reset_password_page.text("Passwords do not match.")).to_be_visible()
        expect(reset_password_page.page).to_have_url(re.compile(r"/reset-password$"))
