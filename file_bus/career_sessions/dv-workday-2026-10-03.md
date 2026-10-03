# DoubleVerify Workday — סשן 2026-10-03

## הושלם

- **Career Bus** — `G:\האחסון שלי\Job_serch_Spark` (שדות טופס + `Noam_Meroz_CV.pdf`).
- **Introduce Yourself** — הוגש אוטומטית (אישור: «Your information has been submitted»). סקריפט: `dv_introduce_submit.py`.
- **סריקת משרות** — 32 משרות ב-DV Careers (`dv_workday_hunt.py` → `dv_hunt_results.json`).
- **דירוג** — `hit_match_detail` מ-Hub; סף הגשה ≥25 (מתיחה) / דילוג &lt;25 או score 5.

### מועמדות עיקריות להגשה (ציון ≥40, לא חסום education)

| ציון | משרה | מיקום | קישור |
|------|------|--------|--------|
| 57 | Data Scientist | Tel Aviv | [JR00001027](https://doubleverify.wd5.myworkdayjobs.com/en-US/DV_Careers/job/Tel-Aviv-Israel/Data-Scientist_JR00001027-1) |
| 57 | Sr. Product Analyst | Tel Aviv | [JR00001076](https://doubleverify.wd5.myworkdayjobs.com/en-US/DV_Careers/job/Tel-Aviv-Israel/Sr-Product-Analyst_JR00001076) |
| 57 | Sr Data Scientist II | Paris | [JR00000919](https://doubleverify.wd5.myworkdayjobs.com/en-US/DV_Careers/job/Paris-France/Sr-Data-Scientist-II_JR00000919-1) |

(עוד ~15 משרות עם ציון 57 סווגו «apply» אך לא ML/תל-אביב — ראה `dv_hunt_results.json`.)

## עדכון סשן 2 (מאושר)

- **`ledger/jobs.json`** — 33 רשומות DoubleVerify + Introduce Yourself (`sync_dv_to_ledger.py`).
- **`applications.jsonl`** — שורה ל-Introduce Yourself.
- **`dv_apply_batch.py`** — GLM לשדות פתוחים; לולאה על 8 משרות → עדיין **login/stuck** בלי `WORKDAY_PASSWORD` או Sign In בפרופיל.
- **JobMaster** — `jobmaster_hunt.py`: 5 משרות, 2 הוגדרו לתור Hub (`submit_form_job` queued).
- **Joblily** — `joblily.com` חנוי; לא ניתן להגיש שם.

## ממתין (סיסמה Workday)

הגדר בסביבה (לא ב-git): `WORKDAY_PASSWORD` + הרץ:

`DV_APPLY_PROFILE_DIR=<career_sessions>\dv_chrome_profile` אחרי Sign In ידני פעם אחת.

## Git

- `form939-local-sandbox/file_bus/career_sessions/` — commit + push לסנדבוקס.

## קבצים

- `form939-local-sandbox\file_bus\career_sessions\dv_session.json`
- `dv_hunt_results.json` — כל 32 המשרות + סטטוס
- `dv_introduce_submit.py`, `dv_workday_hunt.py`, `dv_apply_one.py`
