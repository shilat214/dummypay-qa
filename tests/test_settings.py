import pytest
import time
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
        if config.USER1_EMAIL:
            expect(settings_page.profile).to_contain_text(config.USER1_EMAIL)

    def test_display_name_can_be_changed_and_restored(self, settings_page):
        expect(settings_page.display_name_input).not_to_have_value("")
        original = settings_page.display_name_input.input_value()
        new_name = f"QA {int(time.time())}"  # unique every run

        try:
            settings_page.rename(new_name)
            expect(settings_page.toast("Display name updated.")).to_be_visible()
            expect(settings_page.profile).to_contain_text(new_name)
        finally:
            # restore only if the rename was actually saved
            if new_name in settings_page.profile.inner_text():
                settings_page.rename(original)

    def test_preferred_currency_card_is_shown(self, settings_page):
        expect(settings_page.page.get_by_text("Preferred currency").first).to_be_visible()
        expect(settings_page.currency_select).to_be_visible()

    def test_changing_currency_asks_for_confirmation_and_can_be_cancelled(self, settings_page):
        settings_page.currency_select.click()
        settings_page.page.get_by_role("option").nth(0).click()
        if settings_page.change_button.is_disabled():  # first option was the current currency
            settings_page.currency_select.click()
            settings_page.page.get_by_role("option").nth(1).click()
        settings_page.change_button.click()
        expect(settings_page.confirm_dialog).to_contain_text("no funds are added")
        settings_page.confirm_dialog.get_by_role("button", name="Cancel").click()
        expect(settings_page.confirm_dialog).to_be_hidden()


class TestSettingsNegative:
    pytestmark = pytest.mark.negative

    def test_one_character_display_name_is_rejected(self, settings_page):
        settings_page.rename("A")
        expect(settings_page.text("Display name must be at least 2 characters.")).to_be_visible()

    def test_display_name_over_fifty_characters_is_rejected(self, settings_page):
        settings_page.rename("A" * 51)
        expect(settings_page.text("Display name must be at most 50 characters.")).to_be_visible()

    def test_save_is_disabled_until_the_name_is_edited(self, settings_page):
        expect(settings_page.save_button).to_be_disabled()
