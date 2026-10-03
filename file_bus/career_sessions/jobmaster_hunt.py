"""Scrape JobMaster data-scientist hits, score, queue Hub submit for top matches."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

HUB = Path(r"C:\Users\noam1\Documents\principal-architect-hub")
sys.path.insert(0, str(HUB))
BUS = Path(r"G:\האחסון שלי\Job_serch_Spark")
OUT = Path(__file__).with_name("jobmaster_hunt.json")
SEARCH = "https://www.jobmaster.co.il/jobs/q-data-scientist/"


def _slug(title: str) -> str:
    return ("jobmaster-" + re.sub(r"[^a-z0-9]+", "-", title.lower())[:50]).strip("-")[:70]


def main() -> int:
    from dashboard.career_submit import _chrome_executable, hit_match_detail
    from playwright.sync_api import sync_playwright

    chrome = _chrome_executable()
    kw = {"headless": False, "args": ["--disable-blink-features=AutomationControlled"]}
    if chrome:
        kw["executable_path"] = str(chrome)
    profile = os.environ.get("CAREER_SUBMIT_PROFILE_DIR", "").strip()
    hits: list[dict] = []
    with sync_playwright() as p:
        if profile:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=profile,
                headless=False,
                executable_path=str(chrome) if chrome else None,
                args=kw["args"],
            )
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            closer = ctx
        else:
            browser = p.chromium.launch(**kw)
            page = browser.new_page()
            closer = browser
        page.goto(SEARCH, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3000)
        rows = page.evaluate(
            """() => Array.from(document.querySelectorAll('a[href*="/jobs/"]'))
            .map((a) => ({title: (a.innerText||'').trim(), href: a.href}))
            .filter((r) => r.title.length > 8 && r.href.includes('/jobs/'))"""
        )
        seen: set[str] = set()
        if isinstance(rows, list):
            for row in rows:
                title = str(row.get("title") or "")
                href = str(row.get("href") or "")
                if not title or "data scientist" not in title.lower() and "machine learning" not in title.lower():
                    if "data scientist" not in title.lower() and "learning engineer" not in title.lower():
                        continue
                if href in seen:
                    continue
                seen.add(href)
                hits.append({"title": title, "url": href})
        closer.close()
    scored = []
    for hit in hits[:12]:
        detail = hit_match_detail({"title": hit["title"], "lane": "data_science_junior", "job_text": hit["title"]})
        hit["score"] = int(detail["score"])
        hit["summary"] = detail.get("summary")
        scored.append(hit)
    scored.sort(key=lambda r: -int(r.get("score") or 0))
    OUT.write_text(json.dumps(scored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ledger_path = BUS / "ledger" / "jobs.json"
    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    jobs = data.get("jobs") if isinstance(data.get("jobs"), list) else []
    by_url = {str(j.get("source_url") or ""): j for j in jobs if isinstance(j, dict)}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    queued: list[str] = []
    for hit in scored:
        if int(hit.get("score") or 0) < 25:
            continue
        url = hit["url"]
        if url not in by_url:
            jid = _slug(hit["title"])
            jobs.append(
                {
                    "job_id": jid,
                    "company": "",
                    "title": hit["title"][:160],
                    "source_url": url,
                    "application_type": "web_form",
                    "status": "not_submitted",
                    "match_score": hit["score"],
                    "notes": f"JobMaster hunt {now}. {hit.get('summary')}",
                    "blocker": "",
                }
            )
            by_url[url] = jobs[-1]
            queued.append(jid)
    data["jobs"] = jobs
    data["updated_at_utc"] = now
    data["updated_by"] = "jobmaster_hunt"
    ledger_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.environ["CAREER_DRIVE_BUS_DIR"] = str(BUS)
    from dashboard.career_submit import submit_form_job

    submitted = []
    for jid in queued[:3]:
        res = submit_form_job(jid, confirm="SEND", allow_general=True)
        submitted.append({"job_id": jid, "ok": res.get("ok"), "queued": res.get("queued"), "error": res.get("error_type")})
    print(json.dumps({"hits": len(scored), "queued": queued, "submit": submitted}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
