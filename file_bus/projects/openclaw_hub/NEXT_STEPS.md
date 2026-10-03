# משימות פרויקט — `openclaw_hub` (שליטה OpenClaw)

**הקשר:** מנהל עבודה — דשבורד `:8788`, Hub, טלגרם, תיאום סוכנים.  
**נתיב Hub:** `C:\Users\noam1\Documents\principal-architect-hub`  
**סוכן:** `chief_architect`

## תת-תחומים

| תת-תחום | מה | מסמך | ענף Git |
|---------|-----|------|---------|
| **engineering** | כלים, אורקסטרטור, `/engineering` | [engineering/NEXT_STEPS.md](engineering/NEXT_STEPS.md) | `project/system-engineering` |
| **career** | צייד `/career` | למטה | `project/career-hunt` ✅ דחוף |
| **ops** | restart אחרי env | HUB-OPS-* | `project/openclaw_hub` |

| ID | משימה | סטטוס |
|----|--------|--------|
| HUB-OPS-01 | restart :8788 + טלגרם | 🔄 דשבורד :8788 על `master` (career+engineering); טלגרם — להפעיל מחדש ידנית |
| HUB-OPS-02 | אימות E2E טלגרם → `spend_ledger.jsonl` | ⏳ |
| HUB-GIT-01 | `project/career-hunt` + `project/system-engineering` → `master` | ✅ דחוף |

---

## צייד משרות (career)

**יומן:** `jobs.json` (Spark) — 81 ידני / 37 «הוגש» לא מאומת (סקירה 2026-10-03)

### שלב א — תצפית

| ID | משימה | סטטוס |
|----|--------|--------|
| CAREER-A1 | `fail_class` / problem-report | 🔄 `career_triage`, `test_career_triage_report` |
| CAREER-A2 | screenshot + Playwright trace | ⏳ |
| CAREER-A3 | `confirmed` / `unverified` | 🔄 submit-progress + reclass scripts |
| CAREER-A4 | הצלבה Gmail | ⏳ |

### שלב ב — תור

| ID | משימה | סטטוס |
|----|--------|--------|
| CAREER-B1 | ביטול «ידני סופי» | 🔄 `recover_career_submit`, wide-hunt |
| CAREER-B2 | מנעול Chrome + שחרור תקועות | 🔄 profile מקומי (לא ב-git) |

### שלבים ג–ד

ראה טבלאות CAREER-G* / CAREER-D* בגרסה קודמת — ללא שינוי עד הרצה חיה.

**Hub:** https://github.com/noam2177/principal-architect-hub/tree/project/career-hunt
