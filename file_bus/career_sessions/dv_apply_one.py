"""Apply to one DoubleVerify job via Workday modal flow."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, r"C:\Users\noam1\Documents\principal-architect-hub")
from dashboard.career_submit import _chrome_executable

SESSION = Path(__file__).with_name("dv_session.json")
CV = Path(__file__).with_name("Noam_Meroz_CV.pdf")
_SUCCESS = re.compile(r"thank|submitted|received|application has been", re.I)
URL = sys.argv[1] if len(sys.argv) > 1 else (
    "https://doubleverify.wd5.myworkdayjobs.com/en-US/DV_Careers/job/Tel-Aviv-Israel/Data-Scientist_JR00001027-1"
)


def _accept(page) -> None:
    btn = page.get_by_role("button", name="Accept Cookies")
    if btn.count():
        try:
            btn.first.click(timeout=3_000)
            page.wait_for_timeout(400)
        except Exception:
            pass


def main() -> int:
    answers = json.loads(SESSION.read_text(encoding="utf-8"))["answers"]
    chrome = _chrome_executable()
    kw = {"headless": False, "args": ["--disable-blink-features=AutomationControlled"]}
    if chrome:
        kw["executable_path"] = str(chrome)
    status = "unknown"
    profile = Path(__file__).with_name("dv_chrome_profile")
    profile.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=False,
            executable_path=str(chrome) if chrome else None,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(URL, timeout=60_000)
        page.wait_for_timeout(2500)
        _accept(page)
        page.get_by_role("button", name="Apply").first.click(timeout=10_000)
        page.wait_for_timeout(2000)
        for choice in ("Apply Manually", "Autofill with Resume", "Use My Last Application"):
            btn = page.get_by_role("button", name=choice)
            if btn.count():
                btn.first.click(timeout=8_000)
                page.wait_for_timeout(3000)
                break
        for step in range(15):
            body = page.inner_text("body")[:4000]
            if _SUCCESS.search(body):
                status = "submitted"
                break
            if page.locator('input[type=password]').count():
                status = "login_required"
                break
            if re.search(r"verify you are human|i'm not a robot", body, re.I):
                status = "captcha"
                break
            for label, key in (
                (re.compile(r"Given Name.*Latin", re.I), "first_name"),
                (re.compile(r"Family Name.*Latin", re.I), "last_name"),
                (re.compile("Email", re.I), "email"),
            ):
                loc = page.get_by_role("textbox", name=label)
                if loc.count() and answers.get(key):
                    try:
                        loc.first.fill(answers[key], timeout=2_000)
                    except Exception:
                        pass
            if page.locator("input[type=file]").count():
                try:
                    page.locator("input[type=file]").first.set_input_files(str(CV), timeout=5_000)
                except Exception:
                    pass
            page.evaluate(
                """() => document.querySelectorAll('input[type=checkbox]').forEach((b) => {
                  const t = (b.closest('label')?.innerText || '').toLowerCase();
                  if (t.includes('agree') || t.includes('terms') || t.includes('consent')) b.click();
                })"""
            )
            clicked = False
            for name in ("Submit", "Save and Continue", "Continue", "Next", "Review and Submit"):
                b = page.get_by_role("button", name=re.compile(name, re.I))
                if b.count():
                    try:
                        b.first.click(timeout=6_000)
                        clicked = True
                        page.wait_for_timeout(3000)
                        break
                    except Exception:
                        continue
            if not clicked:
                status = "stuck"
                break
        print(json.dumps({"status": status, "url": page.url, "snippet": page.inner_text("body")[:500]}, ensure_ascii=False))
        page.wait_for_timeout(5000)
        context.close()
    return 0 if status == "submitted" else 2


if __name__ == "__main__":
    sys.exit(main())
