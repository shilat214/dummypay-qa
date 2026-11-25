
import re
import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.regression

class TestHistoryPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_history_page_loads(self, history_page):
        history_page.expect_loaded()

    def test_transaction_count_is_correct(self, history_page):
        text = history_page.transaction_count.inner_text()
        expected_count = int(text.split()[0])
        actual_count = history_page.count_all_transactions()
        assert actual_count == expected_count

    def test_transaction_details(self, history_page):
        history_page.choose_type("Sent")
        if history_page.rows.count() == 0:
            expect(history_page.no_match).to_be_visible()
            return
        amount = history_page.open_first_transaction()
        expect(history_page.detail).to_contain_text("Sent")
        expect(history_page.detail).to_contain_text(amount)

    @pytest.mark.parametrize("type_name", ["Sent", "Received"])
    def test_filter_by_type(self, history_page, type_name):
        history_page.choose_type(type_name)
        if history_page.rows.count() > 0:
            for row in history_page.rows.all():
                assert type_name in row.inner_text()
        else:
            expect(history_page.no_match).to_be_visible()

    @pytest.mark.xfail(
        reason="BUG-HIS-01: Clear does not reset currency filter",
        strict=True
    )
    @pytest.mark.parametrize("currency", ["ILS", "USD", "EUR", "GBP"])
    def test_filter_by_currency(self, history_page, currency):
        history_page.choose_currency(currency)
        expect(history_page.currency_filter).to_contain_text(currency)
        history_page.clear_button.click()
        expect(history_page.currency_filter).to_contain_text("All currencies")

class TestHistoryNegative:
    pytestmark = pytest.mark.negative

    def test_future_date_has_no_transactions(self, history_page):
        history_page.from_date.fill("2099-01-01")
        expect(history_page.no_match).to_be_visible()

    def test_history_requires_login(self, page):
        page.goto("/history")
        expect(page).to_have_url(re.compile(r"/login$"))

    def test_clear_disabled_without_filters(self, history_page):
        expect(history_page.clear_button).to_be_disabled()
