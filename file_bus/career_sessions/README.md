# Career browser sessions (sandbox)

Scripts for operator job applications (DoubleVerify Workday, JobMaster). Data lives in Career Bus on Google Drive.

| Script | Purpose |
|--------|---------|
| `dv_session.json` | Cached form answers + CV path (from Bus) |
| `dv_introduce_submit.py` | Introduce Yourself one-shot |
| `dv_workday_hunt.py` | Scan + score DV postings |
| `sync_dv_to_ledger.py` | Push hunt rows → `ledger/jobs.json` |
| `dv_apply_batch.py` | Apply queue (GLM open fields; set `WORKDAY_PASSWORD` + `DV_APPLY_PROFILE_DIR`) |
| `jobmaster_hunt.py` | Scrape JobMaster + queue Hub `submit_form_job` |

**Joblily:** `joblily.com` is parked (HugeDomains). Use JobMaster / Jobify360 / Hirify instead.
