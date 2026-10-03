# תת-תחום — הנדסת מערכת (`openclaw_hub` / `engineering`)

**פרויקט אב:** `openclaw_hub` (שליטה OpenClaw) — **לא** `project_id` נפרד ב-portfolio.  
**ענף Git:** `project/system-engineering` (כלים ב-`form939-agent-hub`; דשבורד ב-`principal-architect-hub`)  
**תיקייה בריפו:** `form939-agent-hub\engineering\`  
**ריפו Hub:** `C:\Users\noam1\Documents\principal-architect-hub`  
**אח:** צייד משרות → [../NEXT_STEPS.md](../NEXT_STEPS.md) (CAREER-*)  
**ידע:** [PROJECT_KNOWLEDGE.md](PROJECT_KNOWLEDGE.md)

---

## Git — לפני כתיבה

```text
py -3 scripts\git_branch_workflow.py gate -p openclaw_hub
git checkout -b project/system-engineering
```

---

## SYSENG — GLM (פלטפורמה)

| ID | משימה | סטטוס | הערות |
|----|--------|--------|--------|
| SYSENG-GLM-01 | `glm_env.py` + `glm_doctor.py` + בדיקות יחידה | ✅ | |
| SYSENG-GLM-02 | מפעיל: מקור מפתח (z.ai / bigmodel.cn); העתקה נקייה | ⏳ | |
| SYSENG-GLM-03 | `glm_doctor.py --live` | ⏳ | |
| SYSENG-GLM-04 | יישור `GLM_API_BASE` ב-shell + Hub `.env` + restart :8788/טלגרם | ⏳ | Hub בחלון Hub |
| SYSENG-GLM-05 | אורקסטרטור: `orchestrator_main.py run` (GLM מושבת כברירת מחדל — `ORCHESTRATOR_ENABLE_GLM=1`) | ✅ run | לא `--rules-cleanup` עד GLM יציב |
| SYSENG-GLM-06 | רוטציה מפתח/טוקן אם הודבקו בצ'אט | ⏳ | |
| SYSENG-GLM-07 | סנדבוקס `glm_flash` + OpenCode `ZAI_API_KEY` — יישור שרת | ⏳ | `sandbox-lab` |

---

## SYSENG — כלים (vendor / אבחון)

| ID | משימה | סטטוס | הערות |
|----|--------|--------|--------|
| SYSENG-TOOLS-01 | `tools_doctor.py` + `--write-todo` | ✅ | |
| SYSENG-TOOLS-02 | Ponytail, Graphify, Repomix, Secretlint, Semgrep `.venv` | ✅ | `vendor/manifest.json` |
| SYSENG-TOOLS-03 | OmniRoute: שרת + מפתח dashboard (`.env` שורות 30–31) | ⏳ | |
| SYSENG-TOOLS-04 | החלטה: Hermes / OmniRoute — להשאיר או לכבות | ⏳ | מפעיל |
| SYSENG-TOOLS-05 | Semgrep תוסף Cursor: `semgrep_global_shim.ps1` / `semgrep login` | ✅ shim | login נכשל — אופציונלי |
| SYSENG-TOOLS-06 | Graphify pipeline על Hub; Semgrep read-only `hub/`/`dashboard/` | ⏳ | Hub |
| SYSENG-TOOLS-07 | CI: `orchestrator_main.py verify` | 📋 | F939-FUT-06 |
| SYSENG-TOOLS-08 | OmniRoute: סיסמה, `npm audit` | 📋 | F939-FUT-01/02 |

---

## SYSENG — כללים, hooks, מדיניות (תשתית הנדסית)

| ID | משימה | סטטוס | מיקום |
|----|--------|--------|--------|
| SYSENG-RULES-01 | `orchestrator-vendor-tools.mdc` — מקור אמת ל-vendors | ✅ | `.cursor/rules/` |
| SYSENG-RULES-02 | Ponytail, cheap-work-routing, continue-to-end, git-branch, zone-guard | ✅ | לא לערבב עם מוצר |
| SYSENG-RULES-03 | Agent Engineering + concise-agent-prompts + tool-call-fix skills | ✅ | sync מ-vendor |
| SYSENG-RULES-04 | Cursor.directory stack rules (Python/React/Node) | ✅ | sync מאורקסטרטור |
| SYSENG-RULES-05 | ניקוי כללים ב-GLM (`--rules-cleanup`) רק אחרי מפתח + dry-run | ⏳ | guard על core rules בקוד |
| SYSENG-RULES-06 | Semgrep MCP guard / hooks | ✅ | `.cursor/hooks/semgrep-mcp-guard.ps1` |

---

## SYSENG — דשבורד (צפייה ועריכה) — `principal-architect-hub`

| ID | משימה | סטטוס | תיאור |
|----|--------|--------|--------|
| SYSENG-DASH-01 | API קריאה: `latest_run.json` + `vendor/manifest.json` readiness | ✅ | `GET /api/engineering` ב-Hub |
| SYSENG-DASH-02 | עמוד `/engineering` — סטטוס כלים, glm_config, תאריך ריצה | ✅ | ענף Hub `project/system-engineering` |
| SYSENG-DASH-03 | כפתור «הרץ verify» (קריאה ל-orchestrator verify, ללא commit) | ✅ | `POST /api/engineering/verify` |
| SYSENG-DASH-04 | צפייה בכללים: רשימה מ-`.cursor/rules` (read-only) | ⏳ | |
| SYSENG-DASH-05 | עריכה מבוקרת: טיוטת כלל → «אשר שינוי» (טלגרם/מפעיל) | 📋 | לא עריכה חופשית בפרוד |
| SYSENG-DASH-06 | קישור ל-`openclaw_hub/engineering/NEXT_STEPS.md` בדשבורד | 📋 | |

מפרט מכונה: `form939-agent-hub\engineering\config.json` · מסלול דשבורד מתוכנן: `/engineering`

---

## פקודות (ריפו form939-agent-hub)

```powershell
py -3 scripts\git_branch_workflow.py gate -p openclaw_hub
py -3 scripts\glm_doctor.py
py -3 scripts\glm_doctor.py --live
py -3 scripts\tools_doctor.py --write-todo
py -3 scripts\orchestrator_main.py verify
py -3 scripts\orchestrator_main.py run
py -3 scripts\orchestrator_main.py sync-skills
```

---

## הושלם (תשתית) — מזהים ישנים F939-DONE-*

Ponytail, Graphify skill, Repomix, Secretlint, Semgrep venv, Agent Engineering skills, Cursor.directory, OmniRoute install, `.env.example`, Gitleaks skipped — רשום ב-`form939-agent-hub/TODO.md` סעיף «הושלם».
