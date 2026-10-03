"""Merge DV hunt rows into Career Bus ledger/jobs.json (idempotent by source_url)."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BUS = Path(r"G:\האחסון שלי\Job_serch_Spark")
HUNT = Path(__file__).with_name("dv_hunt_results.json")


def _slug(title: str, url: str) -> str:
    tail = url.rstrip("/").split("/")[-1][:60]
    base = re.sub(r"[^a-z0-9]+", "-", title.lower())[:40].strip("-") or "role"
    return f"doubleverify-{base}-{tail}".lower()[:80]


def main() -> int:
    hunt = json.loads(HUNT.read_text(encoding="utf-8"))
    ledger_path = BUS / "ledger" / "jobs.json"
    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        jobs = []
    by_url = {str(j.get("source_url") or "").split("?")[0]: j for j in jobs if isinstance(j, dict)}
    added = updated = 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for row in hunt.get("jobs") or []:
        if not isinstance(row, dict):
            continue
        url = str(row.get("url") or "").split("?")[0]
        if not url:
            continue
        title = str(row.get("title") or "")[:160]
        score = int(row.get("score") or 0)
        action = str(row.get("action") or "")
        status_map = {
            "submitted": "submitted",
            "login_required": "not_submitted",
            "captcha": "blocked",
            "blocked": "blocked",
            "stuck": "blocked",
        }
        st = status_map.get(str(row.get("status") or ""), "not_submitted")
        if action == "skip_low":
            st = "closed" if score < 25 else st
        blocker = ""
        if row.get("status") == "login_required":
            blocker = "Workday: נדרש Sign In לחשבון מועמד לפני Apply."
        elif str(row.get("status") or "") == "blocked":
            blocker = str(row.get("note") or "הגשה אוטומטית נעצרה.")
        job = by_url.get(url)
        if job is None:
            job = {
                "job_id": _slug(title, url),
                "company": "DoubleVerify",
                "title": title,
                "location": "",
                "source_url": url,
                "application_type": "web_form",
                "status": st,
                "match_score": score,
                "notes": f"DV Workday hunt 2026-10-03. {row.get('summary') or ''}"[:500],
                "blocker": blocker,
            }
            jobs.append(job)
            by_url[url] = job
            added += 1
        else:
            job["match_score"] = score
            if blocker:
                job["blocker"] = blocker
            if st == "submitted":
                job["status"] = st
            updated += 1
    # Introduce yourself pool
    intro_url = "https://doubleverify.wd5.myworkdayjobs.com/en-US/DV_Careers/introduceYourself"
    if intro_url not in by_url:
        jobs.append(
            {
                "job_id": "doubleverify-introduce-yourself",
                "company": "DoubleVerify",
                "title": "Introduce Yourself (talent pool)",
                "location": "Israel",
                "source_url": intro_url,
                "application_type": "web_form",
                "status": "submitted",
                "form_submitted_at_utc": now,
                "notes": "הוגש אוטומטית 2026-10-03.",
                "blocker": "",
                "match_score": 50,
            }
        )
        added += 1
    data["jobs"] = jobs
    data["updated_at_utc"] = now
    data["updated_by"] = "dv_workday_session"
    ledger_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "added": added, "updated": updated, "total": len(jobs)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
