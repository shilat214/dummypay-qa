"""Runs LAST (file name sorts last) on purpose.

Supabase signs the user out on every device, so this test would invalidate the saved
sessions of the user it logs in as. We use USER2 and run it after everything else.
"""
import re

import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from utilities import config

pytestmark = [pytest.mark.regression, pytest.mark.positive]


def test_sign_out_returns_to_login_and_blocks_protected_pages(page):
    if not config.USER2_EMAIL:
        pytest.skip("USER2 credentials are not configured.")
    login = LoginPage(page).open().login(config.USER2_EMAIL, config.USER2_PASSWORD)
    dashboard = DashboardPage(page)
    expect(dashboard.heading).to_be_visible()
    dashboard.sign_out()
    expect(page).to_have_url(re.compile(r"/login$"))
    page.goto("/")
    expect(page).to_have_url(re.compile(r"/login$"))
    login.expect_loaded()
