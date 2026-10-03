"""One-shot Introduce Yourself submit on DoubleVerify Workday."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SESSION = Path(__file__).with_name("dv_session.json")
CV = Path(__file__).with_name("Noam_Meroz_CV.pdf")
URL = "https://doubleverify.wd5.myworkdayjobs.com/en-US/DV_Careers/introduceYourself"
_SUCCESS = re.compile(r"thank|received|submitted|success", re.I)


def main() -> int:
    data = json.loads(SESSION.read_text(encoding="utf-8"))
    answers = data["answers"]
    cv = Path(data.get("cv_path") or CV)
    if not cv.is_file():
        cv = CV
    if not cv.is_file():
        print(json.dumps({"ok": False, "error": "cv_missing"}))
        return 1

    import os
    import sys as _sys

    _sys.path.insert(0, r"C:\Users\noam1\Documents\principal-architect-hub")
    from dashboard.career_submit import _chrome_executable
    from playwright.sync_api import sync_playwright

    chrome = _chrome_executable()
    launch_kw = {"headless": False, "args": ["--disable-blink-features=AutomationControlled"]}
    if chrome:
        launch_kw["executable_path"] = str(chrome)

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kw)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(2000)
        for label in ("Accept Cookies",):
            btn = page.get_by_role("button", name=label)
            if btn.count():
                btn.first.click(timeout=5_000)
                page.wait_for_timeout(500)
        country = page.locator('[data-automation-id="countryDropdown"]')
        if country.count() and "Israel" not in (country.first.get_attribute("aria-label") or ""):
            country.first.click()
            page.get_by_role("option", name="Israel").click()
        page.get_by_role("textbox", name=re.compile("Hebrew Given", re.I)).fill("נועם")
        page.get_by_role("textbox", name=re.compile("Hebrew Family", re.I)).fill("מרוז")
        page.get_by_role("textbox", name=re.compile("Given Name.*Latin", re.I)).fill(answers["first_name"])
        page.get_by_role("textbox", name=re.compile("Family Name.*Latin", re.I)).fill(answers["last_name"])
        page.get_by_role("textbox", name="Email").fill(answers["email"])
        page.get_by_role("button", name=re.compile("Phone Device Type", re.I)).click()
        page.get_by_role("option", name="Mobile").click()
        phone = re.sub(r"\D", "", answers.get("phone", ""))
        if phone.startswith("0"):
            phone = phone[1:]
        page.get_by_role("textbox", name="Phone Number").fill(phone)
        page.locator("input[type=file]").set_input_files(str(cv))
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Submit").click()
        page.wait_for_timeout(5000)
        body = page.inner_text("body")[:2500]
        ok = bool(_SUCCESS.search(body))
        print(json.dumps({"ok": ok, "url": page.url, "snippet": body[:400]}, ensure_ascii=False))
        if not ok:
            page.wait_for_timeout(15000)
        browser.close()
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
