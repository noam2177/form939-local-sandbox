"""Queue JobMaster ledger jobs with general CV and wait for Hub submit worker."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HUB = Path(r"C:\Users\noam1\Documents\principal-architect-hub")
sys.path.insert(0, str(HUB))
from hub.glm_metered import load_env

load_env()
os.environ.setdefault("CAREER_DRIVE_BUS_DIR", r"G:\האחסון שלי\Job_serch_Spark")

from dashboard.career_submit import _bus_root, _job, submit_form_job

IDS = [
    "jobmaster--machine-learning-engineer-mle",
    "jobmaster--data-scientist",
]


def main() -> int:
    root = _bus_root()
    if root is None:
        print(json.dumps({"ok": False, "error": "bus_dir_unset"}))
        return 1
    queued = []
    for jid in IDS:
        job = _job(root, jid)
        if job is None:
            queued.append({"job_id": jid, "error": "missing"})
            continue
        if str(job.get("application_type") or "") == "manual":
            queued.append({"job_id": jid, "skipped": "manual"})
            continue
        res = submit_form_job(jid, confirm="SEND", allow_general=True)
        queued.append({"job_id": jid, **res})
    deadline = time.time() + 900
    final = []
    while time.time() < deadline:
        data = json.loads((root / "ledger" / "jobs.json").read_text(encoding="utf-8"))
        rows = [j for j in data.get("jobs") or [] if isinstance(j, dict) and j.get("job_id") in IDS]
        if rows and not any(j.get("status") == "submitting" for j in rows):
            final = [
                {
                    "job_id": j.get("job_id"),
                    "status": j.get("status"),
                    "blocker": (j.get("blocker") or "")[:200],
                }
                for j in rows
            ]
            break
        time.sleep(5)
    print(json.dumps({"queued": queued, "final": final}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
