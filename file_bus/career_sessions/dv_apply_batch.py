"""Apply to scored DV jobs using persistent Chrome + optional GLM for open text."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

SESSION = Path(__file__).with_name("dv_session.json")
HUNT = Path(__file__).with_name("dv_hunt_results.json")
CV = Path(__file__).with_name("Noam_Meroz_CV.pdf")
OUT = Path(__file__).with_name("dv_apply_batch_log.json")
_SUCCESS = re.compile(r"thank|submitted|received|application has been", re.I)
_HUB = Path(r"C:\Users\noam1\Documents\principal-architect-hub")
sys.path.insert(0, str(_HUB))


def _profile_dir() -> Path:
    raw = os.environ.get("CAREER_SUBMIT_PROFILE_DIR", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).with_name("dv_chrome_profile")


def _glm_answer(label: str, job_title: str, note: str) -> str:
    from hub.glm_metered import glm_flash

    prompt = (
        f"Job: {job_title}\nField label: {label}\n"
        f"Candidate note (Hebrew ok, 2-4 sentences, no invented employers): {note[:600]}\n"
        'Return JSON: {"text":"..."}'
    )
    row = glm_flash(prompt, purpose="workday_open_field", max_tokens=280)
    if not row.get("ok"):
        return note[:400]
    blob = str(row.get("text") or row.get("content") or "")
    try:
        parsed = json.loads(blob)
        return str(parsed.get("text") or note)[:500]
    except json.JSONDecodeError:
        return blob[:500] if blob else note[:400]


def _chrome_launch(playwright: Any) -> tuple[Any, Any]:
    from dashboard.career_submit import _chrome_executable

    chrome = _chrome_executable()
    profile = _profile_dir()
    profile.mkdir(parents=True, exist_ok=True)
    ctx = playwright.chromium.launch_persistent_context(
        user_data_dir=str(profile),
        headless=False,
        executable_path=str(chrome) if chrome else None,
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    return ctx, page


def _fill_open_text(page: Any, answers: dict[str, str], title: str) -> None:
    note = answers.get("short_note") or ""
    areas = page.locator("textarea")
    for i in range(min(areas.count(), 6)):
        loc = areas.nth(i)
        try:
            if loc.input_value().strip():
                continue
            label = loc.get_attribute("aria-label") or loc.get_attribute("name") or "cover"
            text = _glm_answer(label, title, note)
            loc.fill(text, timeout=4_000)
        except Exception:
            continue


def _apply_one(page: Any, url: str, answers: dict[str, str], title: str) -> str:
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(2000)
    btn = page.get_by_role("button", name=re.compile(r"^Apply$", re.I))
    if not btn.count():
        return "no_apply"
    btn.first.click(timeout=10_000)
    page.wait_for_timeout(2000)
    for choice in ("Apply Manually", "Autofill with Resume", "Use My Last Application"):
        pick = page.get_by_role("button", name=choice)
        if pick.count():
            pick.first.click(timeout=8_000)
            page.wait_for_timeout(2500)
            break
    pwd = os.environ.get("WORKDAY_PASSWORD", "").strip()
    email = answers.get("email", "")
    if page.locator('input[type=password]').count() and pwd and email:
        try:
            page.get_by_role("textbox", name=re.compile("email", re.I)).first.fill(email)
            page.locator('input[type=password]').first.fill(pwd)
            page.get_by_role("button", name=re.compile(r"^Sign In$", re.I)).last.click(timeout=8_000)
            page.wait_for_timeout(4000)
        except Exception:
            pass
    for step in range(16):
        body = page.inner_text("body")[:4000]
        if _SUCCESS.search(body):
            return "submitted"
        if page.locator('input[type=password]').count() and not pwd:
            return "login_required"
        if re.search(r"verify you are human", body, re.I):
            return "captcha"
        for label, key in (
            (re.compile(r"Given Name.*Latin|First Name", re.I), "first_name"),
            (re.compile(r"Family Name.*Latin|Last Name", re.I), "last_name"),
            (re.compile("Email", re.I), "email"),
        ):
            loc = page.get_by_role("textbox", name=label)
            if loc.count() and answers.get(key):
                try:
                    loc.first.fill(answers[key], timeout=2_000)
                except Exception:
                    pass
        phone = re.sub(r"\D", "", answers.get("phone", ""))
        if phone.startswith("0"):
            phone = phone[1:]
        loc = page.get_by_role("textbox", name=re.compile("Phone Number", re.I))
        if loc.count() and phone:
            try:
                loc.first.fill(phone, timeout=2_000)
            except Exception:
                pass
        if page.locator("input[type=file]").count():
            try:
                page.locator("input[type=file]").first.set_input_files(str(CV), timeout=5_000)
            except Exception:
                pass
        _fill_open_text(page, answers, title)
        page.evaluate(
            """() => document.querySelectorAll('input[type=checkbox]').forEach((b) => {
              const t = (b.closest('label')?.innerText || '').toLowerCase();
              if (t.includes('agree') || t.includes('terms')) b.click();
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
            return "stuck"
        time.sleep(1)
    return "stuck"


def main() -> int:
    from hub.glm_metered import load_env
    from playwright.sync_api import sync_playwright

    load_env()
    answers = json.loads(SESSION.read_text(encoding="utf-8"))["answers"]
    hunt = json.loads(HUNT.read_text(encoding="utf-8"))
    # Priority: Tel Aviv data roles first
    rows = [r for r in hunt.get("jobs") or [] if isinstance(r, dict) and r.get("action") == "apply"]
    rows.sort(key=lambda r: (0 if "data scientist" in str(r.get("title", "")).lower() else 1, -int(r.get("score") or 0)))
    log: list[dict] = []
    with sync_playwright() as p:
        ctx, page = _chrome_launch(p)
        try:
            for row in rows[:8]:
                title = str(row.get("title") or "")
                url = str(row.get("url") or "")
                status = _apply_one(page, url, answers, title)
                log.append({"title": title, "url": url, "status": status})
                if status == "login_required":
                    break
                time.sleep(2)
        finally:
            ctx.close()
    OUT.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # refresh hunt + ledger statuses
    by_url = {str(r.get("url", "")).split("?")[0]: r for r in rows}
    for entry in log:
        u = entry["url"].split("?")[0]
        if u in by_url:
            by_url[u]["status"] = entry["status"]
    HUNT.write_text(json.dumps(hunt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess = __import__("subprocess")
    subprocess.run([sys.executable, str(Path(__file__).with_name("sync_dv_to_ledger.py"))], check=False)
    print(json.dumps({"ok": True, "log": log, "path": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
