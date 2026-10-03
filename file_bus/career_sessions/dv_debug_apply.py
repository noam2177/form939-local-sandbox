import json
import sys
from playwright.sync_api import sync_playwright

sys.path.insert(0, r"C:\Users\noam1\Documents\principal-architect-hub")
from dashboard.career_submit import _chrome_executable

URL = "https://doubleverify.wd5.myworkdayjobs.com/en-US/DV_Careers/job/Tel-Aviv-Israel/Data-Scientist_JR00001027-1"

chrome = _chrome_executable()
with sync_playwright() as p:
    kw = {"headless": False, "args": ["--disable-blink-features=AutomationControlled"]}
    if chrome:
        kw["executable_path"] = str(chrome)
    browser = p.chromium.launch(**kw)
    page = browser.new_page()
    page.goto(URL, timeout=60_000)
    page.wait_for_timeout(4000)
    info = page.evaluate(
        """() => ({
          buttons: [...document.querySelectorAll('button,a')]
            .map((e) => (e.innerText || e.getAttribute('aria-label') || '').trim())
            .filter(Boolean).slice(0, 40),
          automation: [...document.querySelectorAll('[data-automation-id]')]
            .map((e) => e.getAttribute('data-automation-id'))
            .filter((x, i, a) => a.indexOf(x) === i)
        })"""
    )
    print(json.dumps(info, ensure_ascii=False, indent=2))
    btn = page.get_by_role("button", name="Apply")
    if btn.count():
        btn.first.click()
        page.wait_for_timeout(5000)
        print("after apply url:", page.url)
        info2 = page.evaluate(
            """() => ({
              buttons: [...document.querySelectorAll('button,a')]
                .map((e) => (e.innerText || e.getAttribute('aria-label') || '').trim())
                .filter(Boolean).slice(0, 40)
            })"""
        )
        print(json.dumps(info2, ensure_ascii=False, indent=2))
        print(page.inner_text("body")[:2000])
    browser.close()
