import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.regression


class TestHistoryPositive:
    pytestmark = pytest.mark.positive

    @pytest.mark.smoke
    def test_history_page_loads(self, history_page):
        history_page.expect_loaded()

    def test_user_has_at_least_one_transaction_row(self, history_page):
        expect(history_page.rows.first).to_be_visible()

    def test_clicking_a_row_opens_transaction_details(self, history_page):
        history_page.rows.first.click()
        expect(history_page.detail).to_be_visible()
        expect(history_page.detail).to_contain_text("completed")

    def test_type_filter_can_be_applied_and_cleared(self, history_page):
        history_page.rows.first.wait_for()
        total = history_page.rows.count()
        history_page.choose_type("Received")
        expect(history_page.clear_button).to_be_enabled()
        history_page.clear_button.click()
        expect(history_page.rows).to_have_count(total)

    def test_details_dialog_closes_with_escape(self, history_page):
        history_page.rows.first.click()
        history_page.page.keyboard.press("Escape")
        expect(history_page.detail).to_be_hidden()


class TestHistoryNegative:
    pytestmark = pytest.mark.negative

    def test_start_date_in_the_future_matches_nothing(self, history_page):
        history_page.from_date.fill("2099-01-01")
        expect(history_page.no_match).to_be_visible()

    def test_end_date_in_the_distant_past_matches_nothing(self, history_page):
        history_page.to_date.fill("1990-01-01")
        expect(history_page.no_match).to_be_visible()

    def test_clear_button_is_disabled_when_no_filter_is_set(self, history_page):
        expect(history_page.clear_button).to_be_disabled()
