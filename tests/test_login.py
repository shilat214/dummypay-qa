import re
import pytest
from playwright.sync_api import expect
from pages.dashboard_page import DashboardPage
from pages.forgot_password_page import ForgotPasswordPage
from utilities import config
from utilities.data import unknown_email
pytestmark = pytest.mark.regression

class TestLoginPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_login_page_shows_the_form(self, login_page):
        expect(login_page.title_text).to_be_visible()
        expect(login_page.email).to_be_visible()
        expect(login_page.password).to_be_visible()
        expect(login_page.sign_in_button).to_be_enabled()

    @pytest.mark.smoke
    def test_valid_credentials_open_the_dashboard(self, login_page):
        if not config.USER1_EMAIL:
            pytest.skip("USER1 credentials are not configured.")
        login_page.login(config.USER1_EMAIL, config.USER1_PASSWORD)
        dashboard = DashboardPage(login_page.page)
        expect(dashboard.heading).to_be_visible()
        expect(login_page.page).not_to_have_url(re.compile(r"/login"))

    def test_forgot_password_link_opens_reset_request_page(self, login_page):
        login_page.forgot_password_link.click()
        expect(login_page.page).to_have_url(re.compile(r"/forgot-password$"))
        expect(ForgotPasswordPage(login_page.page).send_button).to_be_visible()

    def test_create_accaount_link_open_register_page(self, login_page):
            login_page.create_account_link.click()
            expect(login_page.page).to_have_url(re.compile(r"/register"))
class TestLoginNegative:
    pytestmark = pytest.mark.negative
    def test_wrong_password_is_rejected(self, login_page):
        login_page.login(config.USER1_EMAIL, "wrong-password-123")
        expect(login_page.text("Incorrect email or password.")).to_be_visible()
        expect(login_page.page).to_have_url(re.compile(r"/login$"))

    def test_unknown_email_gets_the_same_generic_error(self, login_page):
        login_page.login(unknown_email(), "Whatever-123!")
        expect(login_page.text("Incorrect email or password.")).to_be_visible()

    def test_empty_form_shows_validation_errors(self, login_page):
        login_page.sign_in_button.click()
        expect(login_page.text("Enter a valid email address.")).to_be_visible()
        expect(login_page.text("Enter your password.")).to_be_visible()

    def test_malformed_email_is_rejected(self, login_page):
        login_page.login("not-an-email", "Whatever-123!")
        expect(login_page.text("Enter a valid email address.")).to_be_visible()

    def test_protected_page_redirects_anonymous_visitor_to_login(self, page):
        page.goto("/wallets")
        expect(page).to_have_url(re.compile(r"/login$"))
