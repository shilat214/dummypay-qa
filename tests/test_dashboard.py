import re

import pytest
from playwright.sync_api import expect

from pages.base_page import NAV_ITEMS
from pages.login_page import LoginPage

pytestmark = pytest.mark.regression


class TestDashboardPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_dashboard_loads_with_welcome_message(self, dashboard_page):
        dashboard_page.expect_loaded()
        expect(dashboard_page.welcome).to_be_visible()

    def test_total_balance_shows_a_money_amount(self, dashboard_page):
        expect(dashboard_page.total_balance).to_contain_text(re.compile(r"[₪$€£]\s?[\d,]+\.\d{2}"))

    def test_user_has_at_least_one_wallet_card(self, dashboard_page):
        expect(dashboard_page.wallet_cards.first).to_be_visible()

    def test_rates_card_shows_last_update_time(self, dashboard_page):
        expect(dashboard_page.rates_card).to_contain_text("Last updated")

    def test_sidebar_contains_all_eight_sections(self, dashboard_page):
        for label in NAV_ITEMS:
            expect(dashboard_page.nav_link(label).first).to_be_visible()


class TestDashboardNegative:
    pytestmark = pytest.mark.negative

    def test_anonymous_visitor_is_redirected_to_login(self, page):
        page.goto("/")
        expect(page).to_have_url(re.compile(r"/login$"))
        LoginPage(page).expect_loaded()

    def test_unknown_route_redirects_signed_in_user_to_dashboard(self, user1_page):
        user1_page.goto("/this-page-does-not-exist")
        expect(user1_page).to_have_url(re.compile(r"/$"))

    def test_signed_in_user_cannot_open_login_page(self, user1_page):
        user1_page.goto("/login")
        expect(user1_page).not_to_have_url(re.compile(r"/login"))
