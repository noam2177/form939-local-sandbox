"""Scan DoubleVerify Workday careers, score hits, apply when above threshold."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

SESSION = Path(__file__).with_name("dv_session.json")
RESULTS = Path(__file__).with_name("dv_hunt_results.json")
BASE = "https://doubleverify.wd5.myworkdayjobs.com/en-US/DV_Careers"
SEARCHES = ("data scientist", "machine learning", "data analyst", "NLP", "analytics")
_SUCCESS = re.compile(r"thank|submitted|received|application has been", re.I)
_LANE_NEEDLES = {
    "data_science_junior": ("data scientist", "data science", "machine learning", "data analyst", "ml ", "analytics"),
    "computational_linguistics": ("nlp", "natural language", "linguist", "speech"),
    "computational_cognition": ("cognitive", "psycholingu"),
}


def _lane(title: str, text: str) -> str:
    blob = f"{title} {text}".lower()
    for lane, needles in _LANE_NEEDLES.items():
        if any(n in blob for n in needles):
            return lane
    return "data_science_junior"


def _chrome_launch(playwright: Any) -> Any:
    sys.path.insert(0, r"C:\Users\noam1\Documents\principal-architect-hub")
    from dashboard.career_submit import _chrome_executable

    chrome = _chrome_executable()
    kw = {"headless": False, "args": ["--disable-blink-features=AutomationControlled"]}
    if chrome:
        kw["executable_path"] = str(chrome)
    return playwright.chromium.launch(**kw)


def _accept_cookies(page: Any) -> None:
    btn = page.get_by_role("button", name="Accept Cookies")
    if btn.count():
        try:
            btn.first.click(timeout=4_000)
            page.wait_for_timeout(400)
        except Exception:
            pass


def _search_jobs(page: Any) -> list[dict[str, str]]:
    seen: set[str] = set()
    hits: list[dict[str, str]] = []
    for query in SEARCHES:
        url = f"{BASE}?q={query.replace(' ', '%20')}"
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        _accept_cookies(page)
        page.wait_for_timeout(2500)
        links = page.evaluate(
            """() => Array.from(document.querySelectorAll('a[data-automation-id="jobTitle"], a[href*="/job/"]'))
            .map((a) => ({title: (a.innerText||'').trim(), href: a.href}))
            .filter((r) => r.title && r.href.includes('/job/'))"""
        )
        if not isinstance(links, list):
            continue
        for row in links:
            if not isinstance(row, dict):
                continue
            href = str(row.get("href") or "").split("?")[0]
            title = str(row.get("title") or "").strip()
            if not href or href in seen:
                continue
            seen.add(href)
            hits.append({"title": title, "url": href})
    # also main listing
    page.goto(BASE, wait_until="domcontentloaded", timeout=60_000)
    _accept_cookies(page)
    page.wait_for_timeout(2000)
    links = page.evaluate(
        """() => Array.from(document.querySelectorAll('a[data-automation-id="jobTitle"]'))
        .map((a) => ({title: (a.innerText||'').trim(), href: a.href}))
        .filter((r) => r.title)"""
    )
    if isinstance(links, list):
        for row in links:
            href = str(row.get("href") or "").split("?")[0]
            title = str(row.get("title") or "").strip()
            if href and href not in seen:
                seen.add(href)
                hits.append({"title": title, "url": href})
    return hits


def _score_hit(title: str, job_text: str) -> dict[str, Any]:
    from dashboard.career_submit import hit_match_detail

    lane = _lane(title, job_text)
    return hit_match_detail({"title": title, "lane": lane, "job_text": job_text})


def _fill_standard(page: Any, answers: dict[str, str]) -> None:
    for label, key in (
        ("Email", "email"),
        ("Given Name", "first_name"),
        ("First Name", "first_name"),
        ("Family Name", "last_name"),
        ("Last Name", "last_name"),
    ):
        loc = page.get_by_role("textbox", name=re.compile(label, re.I))
        if loc.count() and answers.get(key):
            try:
                loc.first.fill(answers[key][:80], timeout=3_000)
            except Exception:
                pass
    phone = re.sub(r"\D", "", answers.get("phone", ""))
    if phone.startswith("0"):
        phone = phone[1:]
    loc = page.get_by_role("textbox", name=re.compile("Phone", re.I))
    if loc.count() and phone:
        try:
            loc.first.fill(phone, timeout=3_000)
        except Exception:
            pass


def _upload_cv(page: Any, cv: Path) -> bool:
    try:
        page.locator("input[type=file]").first.set_input_files(str(cv), timeout=8_000)
        return True
    except Exception:
        return False


def _click_apply(page: Any) -> bool:
    btn = page.get_by_role("button", name=re.compile(r"^Apply$", re.I))
    if not btn.count():
        return False
    try:
        btn.first.click(timeout=8_000)
        page.wait_for_timeout(2000)
    except Exception:
        return False
    for choice in ("Apply Manually", "Autofill with Resume", "Use My Last Application"):
        pick = page.get_by_role("button", name=choice)
        if pick.count():
            try:
                pick.first.click(timeout=8_000)
                page.wait_for_timeout(2500)
                break
            except Exception:
                continue
    return True


def _advance_application(page: Any, answers: dict[str, str], cv: Path, max_steps: int = 12) -> str:
    """Returns: submitted | blocked | captcha | login"""
    for _ in range(max_steps):
        body = page.inner_text("body")[:3000]
        if _SUCCESS.search(body):
            return "submitted"
        if re.search(r"verify you are human|i'm not a robot", body, re.I):
            return "captcha"
        if page.locator('input[type=password]').count() or re.search(
            r"create account/sign in|step 1 of 5", body, re.I
        ):
            return "login_required"
        _fill_standard(page, answers)
        if page.locator("input[type=file]").count():
            _upload_cv(page, cv)
        # terms checkboxes
        try:
            page.evaluate(
                """() => document.querySelectorAll('input[type=checkbox]').forEach((b) => {
                  const t = (b.parentElement?.innerText||'').toLowerCase();
                  if (t.includes('agree') || t.includes('terms') || t.includes('consent')) b.click();
                })"""
            )
        except Exception:
            pass
        clicked = False
        for label in ("Submit", "Save and Continue", "Continue", "Next", "Review", "I Agree"):
            btn = page.get_by_role("button", name=re.compile(label, re.I))
            if btn.count():
                try:
                    btn.first.click(timeout=6_000)
                    clicked = True
                    page.wait_for_timeout(2500)
                    break
                except Exception:
                    continue
        if not clicked:
            return "blocked"
    return "blocked"


def main() -> int:
    data = json.loads(SESSION.read_text(encoding="utf-8"))
    answers = data["answers"]
    cv = Path(__file__).with_name("Noam_Meroz_CV.pdf")
    if not cv.is_file():
        cv = Path(data.get("cv_path") or "")
    if not cv.is_file():
        print(json.dumps({"ok": False, "error": "cv_missing"}))
        return 1

    from playwright.sync_api import sync_playwright

    report: dict[str, Any] = {"intro": "submitted", "jobs": [], "applied": [], "skipped": []}
    with sync_playwright() as p:
        browser = _chrome_launch(p)
        page = browser.new_page()
        hits = _search_jobs(page)
        for hit in hits:
            title = hit["title"]
            page.goto(hit["url"], wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(2000)
            job_text = page.inner_text("body")[:8000]
            detail = _score_hit(title, job_text)
            score = int(detail["score"])
            row = {
                "title": title,
                "url": hit["url"],
                "score": score,
                "summary": detail.get("summary"),
                "action": "skip",
                "status": "",
            }
            if score < 25:
                row["action"] = "skip_low"
            elif score >= 40 or score >= 25:
                row["action"] = "apply"
            if row["action"] != "apply":
                report["skipped"].append(row)
                report["jobs"].append(row)
                continue
            if not _click_apply(page):
                row["status"] = "no_apply_button"
                report["skipped"].append(row)
            else:
                status = _advance_application(page, answers, cv)
                row["status"] = status
                if status == "submitted":
                    report["applied"].append(row)
                else:
                    report["skipped"].append(row)
            report["jobs"].append(row)
            time.sleep(2)
        browser.close()
    RESULTS.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "found": len(hits), "applied": len(report["applied"]), "path": str(RESULTS)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
