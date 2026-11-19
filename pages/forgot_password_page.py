from playwright.sync_api import Locator

from pages.base_page import BasePage


class ForgotPasswordPage(BasePage):
    path = "/forgot-password"

    @property
    def email(self) -> Locator:
        return self.page.get_by_label("Email")

    @property
    def send_button(self) -> Locator:
        return self.page.get_by_role("button", name="Send reset link")

    @property
    def confirmation(self) -> Locator:
        return self.page.get_by_test_id("reset-sent")

    def expect_loaded(self):
        self.send_button.wait_for()

    def request_reset(self, email: str):
        self.email.fill(email)
        self.send_button.click()
        return self

    def mock_recover_endpoint(self) -> dict:
        """Intercept the Supabase recover call so no real e-mail is sent. Returns a call tracker."""
        tracker = {"called": False}

        def handler(route):
            tracker["called"] = True
            route.fulfill(status=200, content_type="application/json", body="{}")

        self.page.route("**/auth/v1/recover**", handler)
        return tracker
