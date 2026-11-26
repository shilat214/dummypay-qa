import pytest
from playwright.sync_api import expect
from utilities import config
pytestmark = pytest.mark.regression
class TestSettingsPositive:
    pytestmark = pytest.mark.positive
    @pytest.mark.smoke

    def test_profile_shows_account_details(self, settings_page):
        settings_page.expect_loaded()
        for field in ("User ID", "Email", "Display name", "Registered", "Preferred currency"):
            expect(settings_page.profile).to_contain_text(field)
        expect(settings_page.display_name_input).not_to_have_value("")
        if config.USER1_EMAIL:
            expect(settings_page.profile).to_contain_text(config.USER1_EMAIL)


    def test_display_name_can_be_changed_and_restored(self, settings_page):
        original = settings_page.display_name_input.input_value()
        new_name = "QA Test" if original != "QA Test" else "QA Check"

        try:
            settings_page.rename(new_name)
            expect(settings_page.profile).to_contain_text(new_name)
        finally:
            if settings_page.display_name_input.input_value() != original:
                settings_page.rename(original)
            settings_page.page.reload()
            expect(settings_page.display_name_input).to_have_value(original)

    def test_preferred_currency_card_is_shown(self, settings_page):
        expect(settings_page.currency_select).to_be_visible()
        expect(settings_page.change_button).to_be_visible()
    
    def test_preferred_currency_can_be_saved(self, settings_page):
        original = settings_page.current_currency()
        new_currency = settings_page.different_currency()
        try:
            settings_page.change_currency(new_currency)
            settings_page.confirm_dialog.get_by_role("button", name="Confirm change").click()

            settings_page.page.reload()
            expect(settings_page.profile).to_contain_text(new_currency)

        finally:
            if settings_page.current_currency() != original:
                settings_page.change_currency(original)
                settings_page.confirm_dialog.get_by_role("button", name="Confirm change").click()
                settings_page.page.reload()

            expect(settings_page.profile).to_contain_text(original)

    def test_changing_currency_asks_for_confirmation_and_can_be_cancelled(self, settings_page):
        original = settings_page.current_currency()

        settings_page.change_currency(settings_page.different_currency())

        expect(settings_page.confirm_dialog).to_contain_text("no funds are added")

        settings_page.confirm_dialog.get_by_role("button", name="Cancel").click()
        expect(settings_page.confirm_dialog).to_be_hidden()

        settings_page.page.reload()
        expect(settings_page.profile).to_contain_text(original)

class TestSettingsNegative:
    pytestmark = pytest.mark.negative
   
    @pytest.mark.parametrize("name, error", [
        ("A", "Display name must be at least 2 characters."),
        ("A" * 51, "Display name must be at most 50 characters.")
    ])
    def test_invalid_name_length(self, settings_page, name, error):
        settings_page.rename(name)
        expect(settings_page.text(error)).to_be_visible()

    def test_save_is_disabled_until_the_name_is_edited(self, settings_page):
        expect(settings_page.save_button).to_be_disabled()

    @pytest.mark.xfail(
        reason="BUG-SET-01: Display name allows fewer than 2 letters",
        strict=True
    )
    @pytest.mark.parametrize("name", ["12345", "..", "A123"])
    def test_name_without_two_letters(self, settings_page, name):
        settings_page.display_name_input.fill(name)
        expect(settings_page.save_button).to_be_disabled()

