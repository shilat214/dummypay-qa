import base64

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
from utilities.api_client import DummyPayApi
from utilities.data import BANK_NAME, TEST_CARD_LAST4


VIEWPORT = {"width": 1920, "height": 1080}


# Gives the plain `page` fixture (login and sign-out tests) the same large window.
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": VIEWPORT}


# Signs in once through the login page and saves the session to .auth/<name>.json.
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


# The saved session of user 1 (signs in once per run).
@pytest.fixture(scope="session")
def user1_state(browser, base_url):
    return _login_and_store(browser, base_url, config.USER1_EMAIL, config.USER1_PASSWORD, "user1")


# The saved session of user 2 (signs in once per run).
@pytest.fixture(scope="session")
def user2_state(browser, base_url):
    return _login_and_store(browser, base_url, config.USER2_EMAIL, config.USER2_PASSWORD, "user2")


# A new browser tab that is already signed in as user 1; closed after the test.
@pytest.fixture
def user1_page(browser, base_url, user1_state):
    context = browser.new_context(base_url=base_url, storage_state=user1_state, viewport=VIEWPORT)
    page = context.new_page()
    yield page
    context.close()


# A new browser tab that is already signed in as user 2; closed after the test.
@pytest.fixture
def user2_page(browser, base_url, user2_state):
    context = browser.new_context(base_url=base_url, storage_state=user2_state, viewport=VIEWPORT)
    page = context.new_page()
    yield page
    context.close()


# The e-mail of user 1.
@pytest.fixture(scope="session")
def user1_email():
    return config.USER1_EMAIL


# The e-mail of user 2.
@pytest.fixture(scope="session")
def user2_email():
    if not config.USER2_EMAIL:
        pytest.skip("USER2_EMAIL is not configured.")
    return config.USER2_EMAIL


# An API client signed in as this user.
def _api_for(email, password, name):
    if not email or not password:
        pytest.skip(f"Credentials for {name} are not configured (.env / CI secrets).")
    api = DummyPayApi()
    api.sign_in(email, password)
    return api


# The API client of user 1 (signs in once per run).
@pytest.fixture(scope="session")
def api_user1():
    return _api_for(config.USER1_EMAIL, config.USER1_PASSWORD, "user1")


# The API client of user 2 (signs in once per run).
@pytest.fixture(scope="session")
def api_user2():
    return _api_for(config.USER2_EMAIL, config.USER2_PASSWORD, "user2")


# Login page, opened without a session.
@pytest.fixture
def login_page(page):
    return LoginPage(page).open()


# Forgot-password page object (not opened yet).
@pytest.fixture
def forgot_password_page(page):
    return ForgotPasswordPage(page)


# Dashboard, opened as user 1.
@pytest.fixture
def dashboard_page(user1_page):
    return DashboardPage(user1_page).open()


# Wallets page, opened as user 1.
@pytest.fixture
def wallets_page(user1_page):
    return WalletsPage(user1_page).open()


# Send Money page, opened as user 1.
@pytest.fixture
def send_page(user1_page):
    return SendMoneyPage(user1_page).open()


# Transaction History page, opened as user 1.
@pytest.fixture
def history_page(user1_page):
    return HistoryPage(user1_page).open()


# Cards page, opened as user 1; test cards are deleted through the API before and after the test.
@pytest.fixture
def cards_page(user1_page, api_user1):
    api_user1.delete_cards(TEST_CARD_LAST4)
    yield CardsPage(user1_page).open()
    api_user1.delete_cards(TEST_CARD_LAST4)


# Bank accounts page, opened as user 1; test accounts are deleted through the API before and after the test.
@pytest.fixture
def bank_page(user1_page, api_user1):
    api_user1.delete_bank_accounts(BANK_NAME)
    yield BankAccountsPage(user1_page).open()
    api_user1.delete_bank_accounts(BANK_NAME)


# Notifications page, opened as user 1.
@pytest.fixture
def notifications_page(user1_page):
    return NotificationsPage(user1_page).open()


# Reset-password page, opened as user 1 so the new-password form is shown.
@pytest.fixture
def reset_password_page(user1_page):
    return ResetPasswordPage(user1_page).open()


# Profile & Settings page, opened as user 1.
@pytest.fixture
def settings_page(user1_page):
    return SettingsPage(user1_page).open()


# Adds a screenshot of the page to the HTML report when a test fails.
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    html = item.config.pluginmanager.getplugin("html")
    page = next((item.funcargs[n] for n in ("user1_page", "user2_page", "page") if n in item.funcargs), None)
    if html is None or page is None:
        return
    try:
        shot = base64.b64encode(page.screenshot()).decode()
        report.extras = getattr(report, "extras", []) + [html.extras.png(shot, "Screenshot at failure")]
    except Exception:
        pass
