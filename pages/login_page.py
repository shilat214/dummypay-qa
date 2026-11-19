from playwright.sync_api import Locator

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/login"

    @property
    def title_text(self) -> Locator:
        return self.page.get_by_text("Sign in", exact=True).first

    @property
    def email(self) -> Locator:
        return self.page.get_by_label("Email")

    @property
    def password(self) -> Locator:
        return self.page.get_by_label("Password")

    @property
    def sign_in_button(self) -> Locator:
        return self.page.get_by_role("button", name="Sign in")

    @property
    def forgot_password_link(self) -> Locator:
        return self.page.get_by_role("link", name="Forgot password?")

    @property
    def simulated_note(self) -> Locator:
        return self.page.get_by_role("note")

    def expect_loaded(self):
        self.title_text.wait_for()

    def login(self, email: str, password: str):
        self.email.fill(email)
        self.password.fill(password)
        self.sign_in_button.click()
        return self
