import html
import inspect
import math
import time
from collections import Counter, defaultdict

import pytest

from utilities.config import BASE_URL

COLORS = {"passed": "#2E9E5B", "failed": "#D64545", "error": "#8E2C2C", "skipped": "#E0A800"}
LABELS = {"passed": "Passed", "failed": "Failed", "error": "Errors", "skipped": "Skipped"}
results = defaultdict(Counter)
started = time.time()

STYLE = """
<style>
  body { font-family: "Segoe UI", Arial, sans-serif; background: #F4F6FA; color: #1F2937; margin: 0; padding: 0 28px 40px; }
  #title { background: #1F4E9E; color: #fff; margin: 0 -28px 12px; padding: 22px 28px; font-size: 26px; }
  h2 { color: #1F4E9E; font-size: 18px; margin-top: 22px; }
  #environment { background: #fff; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.08); border: none; }
  #environment td { border: none; border-bottom: 1px solid #EEF1F6; padding: 8px 14px; color: #1F2937; background: #fff; }
  #results-table { background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.08); border: none; }
  #results-table th { background: #1F4E9E; color: #fff; padding: 10px; border: none; }
  #results-table td { border: none; border-bottom: 1px solid #EEF1F6; padding: 9px 10px; color: #1F2937; }
  #results-table td.col-result { font-weight: 600; }
  .passed, .passed .col-result { color: #2E9E5B !important; }
  .failed, .error, .failed .col-result, .error .col-result { color: #D64545 !important; }
  .dp-cards { display: flex; gap: 18px; flex-wrap: wrap; margin: 8px 0 18px; }
  .dp-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.08); padding: 18px 22px; }
  .dp-donut { display: flex; align-items: center; gap: 24px; }
  .dp-legend div { margin: 6px 0; font-size: 14px; }
  .dp-dot { display: inline-block; width: 11px; height: 11px; border-radius: 50%; margin-right: 8px; }
  .dp-kpis { display: grid; grid-template-columns: repeat(2, 130px); gap: 12px; }
  .dp-kpi { border-radius: 10px; padding: 12px 14px; background: #F4F6FA; }
  .dp-kpi b { display: block; font-size: 24px; }
  .dp-kpi span { font-size: 12px; color: #6B7280; text-transform: uppercase; letter-spacing: .04em; }
  .dp-pages { border-collapse: collapse; min-width: 420px; }
  .dp-pages th { text-align: left; font-size: 12px; color: #6B7280; text-transform: uppercase; padding: 6px 10px; }
  .dp-pages td { padding: 7px 10px; border-top: 1px solid #EEF1F6; font-size: 14px; }
  .dp-bar { display: flex; height: 10px; width: 160px; border-radius: 5px; overflow: hidden; background: #EEF1F6; }
</style>
"""


# Names the page a test belongs to from its file name (tests/test_bank_accounts.py -> Bank Accounts).
def page_of(nodeid: str) -> str:
    name = nodeid.split("::")[0].rsplit("/", 1)[-1].removeprefix("test_").removesuffix(".py")
    return name.replace("zz_", "").replace("_", " ").title()


# Sets the report title.
@pytest.hookimpl(optionalhook=True)
def pytest_html_report_title(report):
    report.title = "DummyPay - UI Test Report"


# Replaces the default environment table with the details that matter for this project.
@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    if not config.pluginmanager.hasplugin("metadata"):
        return
    from pytest_metadata.plugin import metadata_key
    config.stash[metadata_key] = {
        "Site": config.getoption("base_url", default=None) or BASE_URL,
        "Browser": ", ".join(config.getoption("browser", default=None) or ["chromium"]),
        "Tests run": config.getoption("markexpr") or "all",
    }


# Adds the comment written above the test function to its report, to show it as a description.
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    comment = inspect.getcomments(item.function) or ""
    outcome.get_result().description = comment.strip().lstrip("#").strip()


# Counts the result of every test per page.
def pytest_runtest_logreport(report):
    page = page_of(report.nodeid)
    if report.when == "call":
        results[page][report.outcome] += 1
    elif report.when == "setup" and report.outcome != "passed":
        results[page]["error" if report.failed else "skipped"] += 1


# Adds a "Description" column to the results table.
@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_header(cells):
    cells.insert(2, "<th>Description</th>")


# Fills the "Description" column of each test.
@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_row(report, cells):
    cells.insert(2, f"<td>{html.escape(getattr(report, 'description', ''))}</td>")


# Builds the donut chart of the results as an SVG.
def donut(totals: Counter) -> str:
    total = sum(totals.values()) or 1
    radius, circumference, offset, parts = 70, 2 * math.pi * 70, 0.0, []
    for outcome in COLORS:
        length = circumference * totals[outcome] / total
        if length:
            parts.append(f'<circle r="{radius}" cx="90" cy="90" fill="none" stroke="{COLORS[outcome]}" stroke-width="26" '
                         f'stroke-dasharray="{length} {circumference - length}" stroke-dashoffset="{-offset}" '
                         f'transform="rotate(-90 90 90)"/>')
            offset += length
    rate = round(100 * totals["passed"] / total)
    return (f'<svg width="180" height="180" viewBox="0 0 180 180">'
            f'<circle r="{radius}" cx="90" cy="90" fill="none" stroke="#EEF1F6" stroke-width="26"/>{"".join(parts)}'
            f'<text x="90" y="88" text-anchor="middle" font-size="30" font-weight="700" fill="#1F2937">{rate}%</text>'
            f'<text x="90" y="110" text-anchor="middle" font-size="12" fill="#6B7280">passed</text></svg>')


# Builds the results bar of one page.
def bar(counts: Counter) -> str:
    total = sum(counts.values()) or 1
    return '<div class="dp-bar">' + "".join(
        f'<div style="width:{100 * counts[o] / total}%;background:{COLORS[o]}"></div>' for o in COLORS if counts[o]) + "</div>"


# Adds the chart, the totals and the results per page above the results table.
@pytest.hookimpl(optionalhook=True)
def pytest_html_results_summary(prefix, summary, postfix, session):
    totals = sum(results.values(), Counter())
    minutes, seconds = divmod(int(time.time() - started), 60)
    legend = "".join(f'<div><span class="dp-dot" style="background:{COLORS[o]}"></span>{LABELS[o]}: <b>{totals[o]}</b></div>'
                     for o in COLORS)
    kpis = "".join(f'<div class="dp-kpi"><b style="color:{color}">{value}</b><span>{label}</span></div>' for value, label, color in (
        (sum(totals.values()), "Tests", "#1F4E9E"), (totals["passed"], "Passed", COLORS["passed"]),
        (totals["failed"] + totals["error"], "Failed", COLORS["failed"]), (f"{minutes}:{seconds:02d}", "Duration", "#1F2937")))
    rows = "".join(f'<tr><td>{html.escape(page)}</td><td>{sum(c.values())}</td><td>{c["passed"]}</td>'
                   f'<td>{c["failed"] + c["error"]}</td><td>{c["skipped"]}</td><td>{bar(c)}</td></tr>'
                   for page, c in sorted(results.items()))
    prefix.append(STYLE + f"""
      <div class="dp-cards">
        <div class="dp-card dp-donut">{donut(totals)}<div class="dp-legend">{legend}</div></div>
        <div class="dp-card"><div class="dp-kpis">{kpis}</div></div>
        <div class="dp-card"><table class="dp-pages">
          <tr><th>Page</th><th>Tests</th><th>Passed</th><th>Failed</th><th>Skipped</th><th></th></tr>{rows}
        </table></div>
      </div>""")
