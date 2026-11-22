import base64
import uuid

import pytest

from pages.bank_accounts_page import BankAccountsPage
from pages.cards_page import CardsPage
from pages.dashboard_page import DashboardPage
from pages.forgot_password_page import ForgotPasswordPage
from pages.history_page import HistoryPage
from pages.login_page import LoginPage
from pages.notifications_page import NotificationsPage
from pages.reset_password_page import ResetPasswordPage
from pages.send_money_page import SendMoneyPage
from pages.settings_page import SettingsPage
from pages.wallets_page import WalletsPage
from utilities import config
from utilities.api_client import DummyPayApi, new_test_email
from utilities.data import BANK_NAME, TEST_CARD_LAST4


VIEWPORT = {"width": 1920, "height": 1080}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Same large viewport for the plain `page` fixture (login / sign-out tests)."""
    return {**browser_context_args, "viewport": VIEWPORT}
# --------------------------------------------------------------------------- #
# Authentication: log in ONCE per user per session through the UI, store the
# session (storage_state) and reuse it. DummyPay rate-limits sign-ins, so tests
# must not log in repeatedly. Sign-up is intentionally NOT automated.
# --------------------------------------------------------------------------- #


def _login_and_store(browser, base_url, email, password, name):
    if not email or not password:
        pytest.skip(f"Credentials for {name} are not configured (.env / CI secrets).")
    config.AUTH_DIR.mkdir(exist_ok=True)
    path = config.AUTH_DIR / f"{name}.json"
    context = browser.new_context(base_url=base_url, viewport=VIEWPORT)
    page = context.new_page()
    LoginPage(page).open().login(email, password)
    DashboardPage(page).heading.wait_for(timeout=20_000)
    context.storage_state(path=str(path))
    context.close()
    return str(path)


@pytest.fixture(scope="session")
def user1_state(browser, base_url):
    return _login_and_store(browser, base_url, config.USER1_EMAIL, config.USER1_PASSWORD, "user1")


@pytest.fixture(scope="session")
def user2_state(browser, base_url):
    return _login_and_store(browser, base_url, config.USER2_EMAIL, config.USER2_PASSWORD, "user2")


@pytest.fixture
def user1_page(browser, base_url, user1_state):
    context = browser.new_context(base_url=base_url, storage_state=user1_state, viewport=VIEWPORT)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def user2_page(browser, base_url, user2_state):
    context = browser.new_context(base_url=base_url, storage_state=user2_state, viewport=VIEWPORT)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="session")
def user1_email():
    return config.USER1_EMAIL


@pytest.fixture(scope="session")
def user2_email():
    if not config.USER2_EMAIL:
        pytest.skip("USER2_EMAIL is not configured.")
    return config.USER2_EMAIL


# --------------------------------------------------------------------------- #
# API clients (one sign-in per user per session - Supabase rate-limits sign-ins)
# --------------------------------------------------------------------------- #


def _api_for(email, password, name):
    if not config.ANON_KEY:
        pytest.skip("DUMMYPAY_ANON_KEY is not configured (.env / CI secrets).")
    if not email or not password:
        pytest.skip(f"Credentials for {name} are not configured (.env / CI secrets).")
    api = DummyPayApi()
    api.sign_in(email, password)
    return api


@pytest.fixture(scope="session")
def api_user1():
    return _api_for(config.USER1_EMAIL, config.USER1_PASSWORD, "user1")


@pytest.fixture(scope="session")
def api_user2():
    return _api_for(config.USER2_EMAIL, config.USER2_PASSWORD, "user2")


@pytest.fixture
def fresh_user():
    """A brand-new account (ILS, one wallet) registered through the API.

    Used only by nightly tests: accounts are permanent and sign-ups are rate-limited,
    so we create at most a couple per run instead of using the shared accounts.
    """
    if not config.ANON_KEY:
        pytest.skip("DUMMYPAY_ANON_KEY is not configured (.env / CI secrets).")
    email, password = new_test_email(), f"Qa-{uuid.uuid4().hex[:12]}"
    api = DummyPayApi()
    session = api.sign_up(email, password, "QA Fresh User", "ILS")
    if not session or not session.get("access_token"):
        pytest.skip("Sign-up did not return a session (email confirmation is on).")
    return {"email": email, "password": password, "api": api}


@pytest.fixture
def fresh_user_page(browser, base_url, fresh_user):
    """Browser signed in as `fresh_user` (one UI sign-in)."""
    context = browser.new_context(base_url=base_url, viewport=VIEWPORT)
    page = context.new_page()
    LoginPage(page).open().login(fresh_user["email"], fresh_user["password"])
    DashboardPage(page).heading.wait_for(timeout=20_000)
    yield page
    context.close()


# --------------------------------------------------------------------------- #
# Page-object fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def login_page(page):
    return LoginPage(page).open()


@pytest.fixture
def forgot_password_page(page):
    return ForgotPasswordPage(page)


@pytest.fixture
def dashboard_page(user1_page):
    return DashboardPage(user1_page).open()


@pytest.fixture
def wallets_page(user1_page):
    return WalletsPage(user1_page).open()


@pytest.fixture
def send_page(user1_page):
    return SendMoneyPage(user1_page).open()


@pytest.fixture
def history_page(user1_page):
    return HistoryPage(user1_page).open()


@pytest.fixture
def cards_page(user1_page, api_user1):
    """Cards page; test cards are deleted through the API before and after the test."""
    api_user1.delete_cards(TEST_CARD_LAST4)
    yield CardsPage(user1_page).open()
    api_user1.delete_cards(TEST_CARD_LAST4)


@pytest.fixture
def bank_page(user1_page, api_user1):
    """Bank accounts page; the test bank's accounts are deleted through the API before and after."""
    api_user1.delete_bank_accounts(BANK_NAME)
    yield BankAccountsPage(user1_page).open()
    api_user1.delete_bank_accounts(BANK_NAME)


@pytest.fixture
def notifications_page(user1_page):
    return NotificationsPage(user1_page).open()


@pytest.fixture
def reset_password_page(user1_page):
    """Reset page opened with a signed-in session, so the new-password form is shown."""
    return ResetPasswordPage(user1_page).open()


@pytest.fixture
def settings_page(user1_page):
    return SettingsPage(user1_page).open()


# --------------------------------------------------------------------------- #
# HTML report: attach a screenshot to every failed test
# --------------------------------------------------------------------------- #


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    html = item.config.pluginmanager.getplugin("html")
    page = next((item.funcargs[n] for n in ("user1_page", "user2_page", "fresh_user_page", "page") if n in item.funcargs), None)
    if html is None or page is None:
        return
    try:
        shot = base64.b64encode(page.screenshot()).decode()
        report.extras = getattr(report, "extras", []) + [html.extras.png(shot, "Screenshot at failure")]
    except Exception:  # page/context may already be closed
        pass
