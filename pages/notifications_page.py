from playwright.sync_api import Locator

from pages.base_page import BasePage


class NotificationsPage(BasePage):
    path = "/notifications"
    title = "Notifications"

    @property
    def items(self) -> Locator:
        return self.page.get_by_test_id("notification-item")

    @property
    def mark_all_button(self) -> Locator:
        return self.page.get_by_role("button", name="Mark all as read")

    @property
    def all_tab(self) -> Locator:
        return self.page.get_by_role("radio", name="All")

    @property
    def unread_tab(self) -> Locator:
        return self.page.get_by_role("radio", name="Unread")

    @property
    def empty_state(self) -> Locator:
        return self.page.get_by_text("No notifications yet")

    @property
    def caught_up(self) -> Locator:
        return self.page.get_by_text("You're all caught up")

    @property
    def unread_badge(self) -> Locator:
        return self.page.get_by_test_id("unread-badge")

    @property
    def incoming_popup(self) -> Locator:
        return self.page.get_by_test_id("incoming-payment")
