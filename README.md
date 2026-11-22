# DummyPay - UI test automation (Playwright + pytest, Page Object Model)

Final project for the QA Automation course. Target: https://dummypay.vercel.app/

## Structure
```
pages/        one Page Object per page (+ base_page.py)
tests/        test modules per page, conftest.py (fixtures, report hook)
utilities/    config (.env), test data, reusable flows, API client, money helpers
docs/         STP / STD (PDF)
.github/      CI workflow, CODEOWNERS, PR template
pytest.ini    markers, HTML report, screenshots/traces on failure
```

## Setup
```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env      # then fill in the two users
```
Register the two users **once, manually** (sign-up is not automated, per the instructor) with
non-real addresses, e.g. `name@test.dummypay.dev`, and put them in `.env`.

## Run
```powershell
python -m pytest -m smoke                    # fast sanity suite
python -m pytest -m regression               # full functional suite
python -m pytest -m "regression or nightly"  # everything
python -m pytest -m negative                 # only negative tests
python -m pytest --headed --slowmo 300       # watch the browser
python -m pytest --browser firefox           # other browser
```
Report: `reports/report.html` (self-contained, failed tests include a screenshot).
Traces of failures: `test-results/` (`python -m playwright show-trace <trace.zip>`).

## Markers
| marker | meaning | when |
|---|---|---|
| smoke | fast critical checks | every pull request |
| regression | full functional suite | merge to main |
| nightly | slow / data-changing (real transfers, real-time notifications) | nightly schedule |
| positive / negative | happy path / invalid input | filter |

## Design decisions
* Sign-in is done **once per session** and the session is re-used (`storage_state`), because DummyPay rate-limits sign-ins.
* **UI or API - whatever is simpler.** Tests check the UI; the REST API is used only where it is
  simpler and more reliable: reading the expected values from the server (balances, totals, rates,
  transactions) and deleting test cards / bank accounts before and after each test.
* Money is fictional; transfers are tiny (1 unit) between the two test users.
* `test_zz_sign_out.py` runs last: signing out invalidates that user's other sessions.
* Exchange rates are real and change, so tests never hard-code amounts: the expected value is read
  from the server at test time and compared with what the page shows.
* Sign-up is **not** automated (per the instructor); the two test users are registered manually.

## GitHub setup (code review protection)
1. Create the repo, push `main`, add team members under *Settings -> Collaborators*.
2. *Settings -> Branches -> Add rule* for `main`: require a pull request, require 1 approval,
   require review from Code Owners, require status check **tests**, block force pushes.
3. Edit `.github/CODEOWNERS` with the real usernames.
4. *Settings -> Secrets and variables -> Actions*: add `USER1_EMAIL`, `USER1_PASSWORD`, `USER2_EMAIL`, `USER2_PASSWORD`.
   The public API key from the assignment is used by default (override with `DUMMYPAY_ANON_KEY` if needed).
