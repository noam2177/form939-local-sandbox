"""Workday batch: optional WORKDAY_PASSWORD; else 3 min manual Sign In in headed browser."""
from __future__ import annotations

import os
import sys
from pathlib import Path

SESSION_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(r"C:\Users\noam1\Documents\principal-architect-hub")))
from hub.glm_metered import load_env

load_env()
# Local secrets (gitignored): WORKDAY_PASSWORD=...
local_env = SESSION_DIR / ".env"
if local_env.is_file():
    for line in local_env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

if not os.environ.get("WORKDAY_PASSWORD", "").strip():
    print("WORKDAY_PASSWORD not set — opening browser for manual Sign In (180s)...", flush=True)
    from playwright.sync_api import sync_playwright
    from dashboard.career_submit import _chrome_executable

    url = (
        "https://doubleverify.wd5.myworkdayjobs.com/en-US/DV_Careers/job/"
        "Tel-Aviv-Israel/Data-Scientist_JR00001027-1"
    )
    profile = SESSION_DIR / "dv_chrome_profile"
    profile.mkdir(parents=True, exist_ok=True)
    chrome = _chrome_executable()
    kw = {"headless": False, "args": ["--disable-blink-features=AutomationControlled"]}
    if chrome:
        kw["executable_path"] = str(chrome)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(user_data_dir=str(profile), **kw)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(url, timeout=60_000)
        page.get_by_role("button", name="Sign In").first.click(timeout=8_000)
        print("Complete Sign In in the browser window...", flush=True)
        for _ in range(36):
            page.wait_for_timeout(5_000)
            if not page.locator('input[type=password]').count():
                break
        ctx.close()

os.environ["DV_APPLY_PROFILE_DIR"] = str(SESSION_DIR / "dv_chrome_profile")
from dv_apply_batch import main

raise SystemExit(main())
