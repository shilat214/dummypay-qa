import re

import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from pages.notifications_page import NotificationsPage
from utilities.flows import send_money

pytestmark = pytest.mark.regression


class TestNotificationsPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_page_loads_with_tabs_and_mark_all_button(self, notifications_page):
        notifications_page.expect_loaded()
        expect(notifications_page.all_tab).to_be_visible()
        expect(notifications_page.unread_tab).to_be_visible()
        expect(notifications_page.mark_all_button).to_be_visible()

    def test_unread_tab_shows_items_or_caught_up_message(self, notifications_page):
        notifications_page.unread_tab.click()
        expect(notifications_page.items.first.or_(notifications_page.caught_up)).to_be_visible()

    @pytest.mark.nightly
    def test_recipient_sees_popup_with_sender_details_in_real_time(self, user1_page, user2_page, user1_email, user2_email):
        DashboardPage(user2_page).open().expect_loaded()
        send_money(user1_page, user2_email, "1")
        popup = NotificationsPage(user2_page).incoming_popup
        expect(popup).to_be_visible(timeout=20_000)
        expect(popup).to_contain_text(user1_email)
        expect(popup.get_by_test_id("incoming-amount")).to_be_visible()

    @pytest.mark.nightly
    def test_popup_can_be_marked_as_read_and_stays_in_notification_centre(self, user1_page, user2_page, user1_email, user2_email):
        DashboardPage(user2_page).open().expect_loaded()
        send_money(user1_page, user2_email, "1")
        popup = NotificationsPage(user2_page).incoming_popup
        expect(popup).to_be_visible(timeout=20_000)
        popup.get_by_role("button", name="Mark as read").click()
        expect(popup).to_be_hidden()
        centre = NotificationsPage(user2_page).open()
        expect(centre.items.first).to_contain_text(user1_email)
        expect(centre.items.first).to_have_attribute("data-read", "true")


class TestNotificationsNegative:
    pytestmark = pytest.mark.negative

    @pytest.mark.nightly
    def test_sender_gets_no_popup_for_own_transfer(self, user1_page, user2_email):
        send_money(user1_page, user2_email, "1")
        expect(NotificationsPage(user1_page).incoming_popup).to_have_count(0)

    def test_mark_all_is_disabled_when_nothing_is_unread(self, notifications_page):
        if notifications_page.mark_all_button.is_enabled():
            notifications_page.mark_all_button.click()
        expect(notifications_page.mark_all_button).to_be_disabled()

    def test_anonymous_visitor_cannot_open_notifications(self, page):
        page.goto("/notifications")
        expect(page).to_have_url(re.compile(r"/login$"))
