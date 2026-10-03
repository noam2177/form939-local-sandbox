"""Open JobMaster login in career_submit Chrome profile (headed)."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

HUB = Path(r"C:\Users\noam1\Documents\principal-architect-hub")
sys.path.insert(0, str(HUB))
from hub.glm_metered import load_env

load_env()
profile = os.environ.get("CAREER_SUBMIT_PROFILE_DIR", "").strip()
if not profile:
    print("CAREER_SUBMIT_PROFILE_DIR missing")
    raise SystemExit(1)
from dashboard.career_submit import _chrome_executable
from playwright.sync_api import sync_playwright

chrome = _chrome_executable()
kw = {"headless": False, "args": ["--disable-blink-features=AutomationControlled"]}
if chrome:
    kw["executable_path"] = str(chrome)
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(user_data_dir=profile, **kw)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.jobmaster.co.il/jobs/", timeout=60_000)
    link = page.get_by_role("link", name=re.compile(r"התחבר|login", re.I))
    if link.count():
        link.first.click(timeout=10_000)
    print("Sign in to JobMaster, then close the browser window.", flush=True)
    page.wait_for_timeout(180_000)
    ctx.close()
