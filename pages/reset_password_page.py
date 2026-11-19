from playwright.sync_api import Locator

from pages.base_page import BasePage


class ResetPasswordPage(BasePage):
    """Landing page of the emailed reset link.

    Without a recovery session it shows "link invalid". Any signed-in session makes it show the
    new-password form, which lets us test the form without sending e-mails or changing a password
    (tests here only trigger client-side validation, they never submit a valid new password).
    """

    path = "/reset-password"

    # --- form state (a session exists)
    @property
    def title_text(self) -> Locator:
        return self.page.get_by_text("Choose a new password", exact=True)

    @property
    def account_note(self) -> Locator:
        return self.page.get_by_text("Resetting the password for")

    @property
    def new_password(self) -> Locator:
        return self.page.get_by_label("New password", exact=True)

    @property
    def confirm_password(self) -> Locator:
        return self.page.get_by_label("Confirm new password")

    @property
    def update_button(self) -> Locator:
        return self.page.get_by_role("button", name="Update password")

    @property
    def password_hint(self) -> Locator:
        return self.page.get_by_text("At least 8 characters.")

    @property
    def back_to_sign_in(self) -> Locator:
        return self.page.get_by_role("link", name="Back to sign in")

    # --- invalid-link state (no session)
    @property
    def invalid_link_message(self) -> Locator:
        return self.page.get_by_text("This link is invalid or has expired.")

    @property
    def request_new_link(self) -> Locator:
        return self.page.get_by_role("link", name="Request a new link")

    def expect_loaded(self):
        self.title_text.wait_for()

    def try_password(self, password: str, confirm: str):
        self.new_password.fill(password)
        self.confirm_password.fill(confirm)
        self.update_button.click()
        return self
