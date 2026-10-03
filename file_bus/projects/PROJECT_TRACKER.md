# מעקב פרויקטים

עודכן: 2026-09-28 09:30 (שעון מקומי).

שעות נרשמות רק מחלון שעון שאפשר לתחום. אין המרה של קומיטים ישנים לשעות. תקציב הוא יעד, לא זמן שכבר עבדנו.

| project_id | שעות רשומות | מקור |
| --- | --- | --- |
| anscombe-check | 0.44 | 00:13–00:36, ואז 22:22–22:39 |
| he-nlp | 0.14 | 00:36–00:55, ואז 22:22–22:39 |
| bracket-check | 0.05 | חלון 00:36–00:55 |
| csv-sum | 0.08 | 00:36–00:55, ואז 22:22–22:39 |
| tfidf-rank | 0.12 | חלון 22:22–22:39 |
| he-segment | 0.55 | 00:36–00:55, 01:03–01:29, ואז 22:22–22:39 |
| bloomgrid, rsvp, openclaw_hub, life_widget, form_autofill, hadash_gate | לא נרשמו | יש תאריכי פעילות, אין שעון |

סכום רשום: **1.38**. להוסיף שורה ב-`HOURS.jsonl` בסוף כל ישיבה.

## משימות פרויקט — # סקירה (2026-10-03)

סקירה אחרי ניתוח **GLM · כלים שהותקנו · צייד משרות**. פירוט מלא (בלי קיצור מידע) ב-`file_bus/projects/<project_id>/NEXT_STEPS.md`.

| project_id | על מה המשימות | עדיפות | מסמך |
| --- | --- | --- | --- |
| **`openclaw_hub`** | **שליטה OpenClaw** — דשבורד, טלגרם, צייד; תת-תחום **engineering** לכלים | **P0** eng · **P1** career | [openclaw_hub/NEXT_STEPS.md](openclaw_hub/NEXT_STEPS.md) |
| ↳ `engineering` | כלים, כללים, אורקסטרטור, GLM, `/engineering` בדשבורד | P0 | [openclaw_hub/engineering/NEXT_STEPS.md](openclaw_hub/engineering/NEXT_STEPS.md) |
| `openclaw_shell` | חלון Cursor על `form939-agent-hub` | — | [openclaw_shell/NEXT_STEPS.md](openclaw_shell/NEXT_STEPS.md) |
| `presentation-builder` | מצגות + צ'אט GLM (צרכן מפתח) | P2 | [presentation-builder/NEXT_STEPS.md](presentation-builder/NEXT_STEPS.md) |
| `sandbox-lab` | `glm_flash`, OpenCode env | P2 | [sandbox-lab/NEXT_STEPS.md](sandbox-lab/NEXT_STEPS.md) |

**תקציר מצב (שמור מהסקירה):**

- **GLM:** מפתח z.ai לא עובד מול bigmodel.cn (401). shell `.env` ו-Hub `.env` — מפתחים שונים ושרתים שונים. שירותים רצים קוראים Hub `.env` — צריך restart אחרי עדכון.
- **כלים:** רוב ה-vendors עובדים; OmniRoute/Hermes — החלטת מפעיל; Semgrep תוסף Cursor דורש login או shim (`semgrep_global_shim.ps1`).
- **צייד:** 81/148 «ידני» (תור לא מנסה שוב); 37 «הוגש» בלי אישור אתר; קוד ב-`career_submit.py` וב-Hub.

**סדר מומלץ:** `openclaw_hub/engineering` (GLM+כלים) → HUB-OPS restart → career א–ב.  
**ענף כלים:** `project/system-engineering` על `form939-agent-hub` (תיקייה `engineering/`).

---

## משחק C · `bloomgrid`

- מהות: פאזל בלוקים. אופליין, בלי חשבון. מסלול חנות Play.
- סוכן: `game_dev_agent`
- שלב נוכחי: 12 בודקים בבדיקה סגורה. לא נסגר בלי ראיה.
- שלבים קודמים: ידע נטען, עטיפת אנדרואיד בלי הידור APK, טיוטת פרטיות.
- מטרה: 14 יום בדיקה, ואז פרסום.
- שעות: לא נרשמו. קומיט ציבורי אחרון שנראה: 2026-09-08.

## הזמנות RSVP · `rsvp`

- מהות: רשימת אורחים חיה ואחוז מענה. מסלול ההכנסה.
- סוכן: `rsvp_dev_agent`
- שלב נוכחי: שער «תכנון הרצת טסטים» פתוח בלוח. ב-2026-09-24 רצו 16 vitest (סירוב בוואטסאפ, טלפון אחד לשורה).
- שלבים קודמים: סטטוס מוצר נקרא.
- מטרה: בלי מודל בזמן ריצה, בלי רב-דייר עד שער E2.
- שעות: לא נרשמו.

## מנהל עבודה OpenClaw · `openclaw_hub`

- מהות: דשבורד הסוכנים. מתאם, לא מוצר הכנסה.
- סוכן: `chief_architect`
- שלב נוכחי: שיפור דשבורד רק אם יש חיכוך (פחות קליקים, פקד שבור). בלי עיצוב סרק.
- שלבים קודמים: סטטוס נרשם.
- 2026-09-29: תיקון ניתוב צ׳אט (Ollama כבוי + GLM / ראיון), אזור Sagole ב-`SAGOLE_ZONE=1`, דירוג מודל מקומי, 525 טסטים ירוקים.
- מטרה: קונסול שאפשר להפעיל בלי לחזור על אותה עבודה.
- שעות: לא נרשמו.

## ווידג'ט משימות · `life_widget`

- מהות: משימות אישיות. לא יוזמה A.
- סוכן: `personal_projects_agent`
- שלב נוכחי: UX — התחלה מהירה ב-/life, empty state actionable (2026-09-30).
- שלבים קודמים: סטטוס נרשם.
- מטרה: משימות אישיות בנפרד מהמשרד.
- שעות: לא נרשמו.

## מילוי טפסים · `form_autofill`

- מהות: לזהות קובץ, לשאול על שדות חסרים, למלא עותק. סינתטי בלבד.
- סוכן: `app_dev_agent`
- שלב נוכחי: ראיון שדות + רמז FORM_FILL_PROFILE.
- שלבים קודמים: זיהוי `synthetic_invite.docx` — שם מלא, טלפון.
- מטרה: עותק ממולא במחשב, בלי תיקיות משרד.
- שעות: לא נרשמו.

## שער סוג מסמך · `hadash_gate`

- מהות: שער לפני חילוץ, על דמה. בלי קורפוס משרד.
- סוכן: `sandbox_researcher`
- שלב נוכחי: סקירת ארכיטקט. המימוש וההשוואות כבר סומנו.
- שלבים קודמים: טיוטה מקומית נדחתה ולא יושמה. שער, שדות עלות, השוואה משולשת, השוואת ענן מול מקומי מקובץ קיים.
- מטרה: מדידה חוזרת על דמה. לא מממשים `src/` מכאן.
- שעות: לא נרשמו.

## תיק עבודות · `ds_portfolio`

- מהות: עבודה ציבורית תחת `noam2177`. מתחילים בקטן ומעמיקים. הטקסט הציבורי לא מספר מי כתב אותו.
- סוכן: `personal_projects_agent`
- שלב נוכחי: חמישה ריפו עלו ל-`noam2177`, כולל `tfidf-rank`.
- שלבים קודמים: `anscombe-check` (אותו סיכום, צורה אחרת).
- מטרה: כל ישיבה סוגרת שלב שאפשר להריץ.
- שעות רשומות: 0.83 על הריפו הקטנים. `he-segment` נספר לחוד.

| ריפו | שלב | שעות |
| --- | --- | --- |
| [anscombe-check](https://github.com/noam2177/anscombe-check) | נקודה רחוקה, טבעת ב-SVG, ו-R² ליד pearson | 0.44 |
| [bracket-check](https://github.com/noam2177/bracket-check) | מקום השבירה, ואז `closer` מול `open` | 0.05 |
| [csv-sum](https://github.com/noam2177/csv-sum) | סטיית תקן, ואז חציון | 0.08 |
| [he-nlp](https://github.com/noam2177/he-nlp) | ו׳ ועוד אות, ואז ש׳ ועוד אות. `כש` נשאר חיתוך אחד | 0.14 |
| [tfidf-rank](https://github.com/noam2177/tfidf-rank) | Dice, ואז Overlap על אותם טריגרמים | 0.12 |

דלת התיק: [portfolio](https://github.com/noam2177/portfolio). משחקים שכבר היו ציבוריים נכנסו לשם: BloomGrid, טורניר, CoCLZ. צייד המשרות הציבורי הוא [job-board](https://github.com/noam2177/job-board) על דוגמה מומצאת. לוח המשרות האמיתי וקורות החיים לא עלו.

2026-09-28: צעד צמוד בכל ריפו קטן, בלי קובץ חדש. `qwen2.5:7b` כתב את החציון. ל-R² הוא הציע NumPy, והחישוב נשאר `pearson` בריבוע. המבחן הקפוא נשאר 64 / 36 / 36. ב-BloomGrid האבנים מצוירות כפאות עם באר שקועה ורקע עמוק יותר.

2026-09-28 01:20: עוד צעד צמוד. מינימום ומקסימום, הסוגר הצפוי, נקודות מעל מרחק 2, ה׳ אחרי ש׳+אות, חלקי תגי השגיאה, אי-הסכמה בין קוסינוס ל-Jaccard, וספירת טפסים. המבחן הקפוא נשאר 64. חלון Godot נפתח על BloomGrid.

2026-09-28 01:20: עוד צעד צמוד. מינימום ומקסימום, הסוגר הצפוי, נקודות מעל מרחק 2, ה׳ אחרי ש׳+אות, חלקי תגי השגיאה, אי-הסכמה בין קוסינוס ל-Jaccard, וספירת טפסים. המבחן הקפוא נשאר 64. חלון Godot נפתח על BloomGrid.

המאגר שממנו ממשיכים: `Documents\GitHub\portfolio\projects.json`. פרויקט חדש נכנס עם `python register.py`. הכלל אצל הסוכן: `.cursor/rules/project-registry.mdc`.

## בור-צלף · `burrow-sniper`

- מהות: צלף מנקודה אחת. מחילות, מטרות נייחות, מסיחים, עשרה רובים, חמש יכולות.
- סוכן: `personal_projects_agent`
- שלב נוכחי: נשקים מסודרים לפי טווח, עם כוח, דיוק, טווח, ועלות סטמינה לירייה.
- שלבים קודמים: עמוד ראשון נפתח. Flash תכנן ולא החזיר עמוד רץ.
- מטרה: סיבוב הבא על אותו ריפו, לא משחק חדש.
- ריפו: [sniper-burrow](https://github.com/noam2177/sniper-burrow)
- שעות: לא נרשמו.

## פיצול תחיליות · `he_segment`

- מהות: כלי שמפצל תחיליות עבריות מהגזע ומודד איפה הוא טועה. דאטה ובלשנות על אותו זהב.
- סוכן: `personal_projects_agent`
- יעד סופי: סט מבחן קפוא, שלוש מערכות (בייסליין, לקסיקון, מודל תווים), טבלת precision/recall לפי סוג שגיאה.
- תקציב: 120–200 שעות עד הטבלה וההערה שאחריה. זה יעד, לא זמן שעבד.
- שלב נוכחי: המבחן קפוא. טסט נועל 64 / 36 / 36.
- שלבים קודמים: סכמה ו-15 טוקנים. תגי שגיאה. פיצול קבוע. לקסיקון מ-train. מודל תווים מ-train. הערה על חמש מילים.
- הבא: להגדיל רק את train, בלי לרדת מ-64 על המבחן הקפוא. 3272 השורות שהורידו ל-53 נשארות בחוץ. ב-2026-09-28 נרשמה מסננת כמועמדת לפרויקט הראשי. הצעד כאן נשאר עד שהמפעיל מזיז את התקציב.
- ריפו: [he-segment](https://github.com/noam2177/he-segment)
- שעות רשומות: 0.55

השלבים המלאים, מהסוף אחורה, ב-`PLAN.md` של הריפו. טיוטת הסדר הגיעה מ-`qwen2.5:7b` וקוצרה. `qwen2.5:3b` לא ענה על המשימה.

שני הדברים הקלים (`bracket-check`, `csv-sum`) תוכננו בקריאה ל-GLM-5.3-Flash. הקריאה הראשונה חזרה ריקה. בשנייה העיצוב הגיע ונקטע לפני JSON סופי. הקוד שעלה הוא העיצוב הזה, והטסטים עברו.

2026-09-27 22:22–22:39: `qwen2.5:7b` אישר TF-IDF, קוסינוס, Jaccard, והצעדים הקטנים. GLM-5.3-Flash לא נקרא: תקרת `max_calls` על היומן (1085 מול 24), בלי חיוב. הדולרים בישיבה היו 4.04 מתוך 5.

## מסננת · `masnenet`

- מהות: פיענוח עברי אחד. מחפש מקבל רשימה חינמית בלי הרשמה, כרטיס אחד למשרה. חברת השמה מקבלת ביד רק «שלח».
- סוכן: `personal_projects_agent`
- יעד: שתי טבלאות על זהב קפוא — דיוק איחוד משרות, ודיוק «שלח» — ואז הערת שגיאה. פיצול התחיליות נשאר שער.
- תקציב: 160 שעות יעד, טווח 140–190. מחליף את המשך 120–200 של `he_segment` אחרי אישור, ולא נוסף עליו. הסורק של 150 המקורות נשאר מחוץ לתקציב.
- שלב נוכחי: דיל ב-`DEAL.md`. תא הרעיון ב-`PRODUCT.md`. סדר הסשן ב-`PLAN.md`.
- הבא: 40 זוגות קפואים, עם סוג העסקה ושיוך קודם.
- מחקר 2026-09-28: הסוכן רץ שלוש פעמים, השומר חסם xss, אין פתק. המספרים בדיל הם מתקנונים פומביים.
- שעות רשומות: 0.
- עלות בנייה: 0 ₪. ריצה מקומית במלואה. כ-66% משעות הבנייה ניתנות לטיוטה ב-`qwen2.5:7b`. הכנסה בשערים הראשונים: 0 בכוונה.
- GLM: ביקורת האדריכל לא רצה. 1093 קריאות מול 24, ו-$4.05 מתוך $5.

<!-- project:burrow-sniper -->
## בור-צלף · `burrow-sniper`

- שלב: עזרה H/? + 12 רובים + בדיקות
- הבא: B3 שלב היסטורי
- נתיב: `C:\Users\noam1\Documents\GitHub\sniper-burrow`
<!-- /project:burrow-sniper -->

<!-- project:hybrid-cloud-bus -->
## אוטובוס היברידי · `hybrid-cloud-bus`

- שלב: dry run מקומי עבר: A נדחה, B נלקח מיד, C נלקח ב-60 שניות. לא נפרס.
- הבא: כותב Drive שנבדק, ואז image מ-cloud_node/Dockerfile. בלי gcloud עד אז.
- נתיב: `C:\Users\noam1\Documents\principal-architect-hub`
<!-- /project:hybrid-cloud-bus -->

<!-- project:personal-site -->
## אתר אישי · `personal-site`

- שלב: דף מעוצב מקורות החיים הכלליים, על GitHub Pages.
- הבא: רק אם המפעיל מבקש להוריד טלפון או דואל מהדף הציבורי.
- נתיב: `C:\Users\noam1\Documents\GitHub\noam2177.github.io`
<!-- /project:personal-site -->

<!-- project:masnenet -->
## מסננת · `masnenet`

- שלב: דיל כתוב. זהב עדיין לא נעול.
- הבא: 40 זוגות קפואים, עם סוג העסקה ושיוך קודם.
- נתיב: `C:\Users\noam1\Documents\GitHub\masnenet`
<!-- /project:masnenet -->

<!-- project:finance-router -->
## סוכן ניתוב פיננסי · `finance-router`

- שלב: מוגדר בתיק. עדיין בלי ריפו.
- הבא: עותק קפוא של Financial PhraseBank, מסווג זול, וטבלת דיוק מול אחוז השורות שנשארות מקומיות.
- נתיב: `C:\Users\noam1\Documents\GitHub\finance-router`
<!-- /project:finance-router -->

<!-- project:job-hub-cloud -->
## job-hub-cloud · `job-hub-cloud`

- שלב: G0+B Q DDL live; dry-run 111 jobs reconciled; apply+P1+P4+P5 live pending
- הבא: Noam: backfill --apply, BotFather+VM, inbox_raw watcher, P5 Hebrew eval
- נתיב: `C:\Users\noam1\Documents\GitHub\job-hub-cloud`
<!-- /project:job-hub-cloud -->

<!-- project:bot-task-manger -->
## Bot_TaskManger · בוט משימות · `bot-task-manger`

- שלב: טלגרם: תפריט ממוספר, קליטה חופשית של כמה משימות, עריכה מלאה, תזכורות מתוזמנות, מייל דחוף עם הזמנה ליומן
- הבא: להתקין faster-whisper לתמלול הקלטות; לבדוק מייל דחוף ראשון מול Gmail
- נתיב: `C:\Users\noam1\Documents\principal-architect-hub\hub\telegram_life.py`
<!-- /project:bot-task-manger -->

<!-- project:rsvp -->
## מי מגיע (Mi-Magia-VIP) · `rsvp`

- שלב: ריפו noam2177/Mi-Magia-VIP. main=wedding-v1 (החתונה), product-v2=מוצר+מיתוג, שניהם ב-GitHub. mi-magia-vip-legacy = ישן, קריאה בלבד.
- הבא: Phase 1: ענף unify מ-main + שכבת המוצר כתוספת; השוואה ויזואלית של /e/daniel-tomer; סיבוב מפתחות Supabase.
- נתיב: `C:\Users\noam1\Documents\GitHub\danielntomerafter-main`
<!-- /project:rsvp -->

## בוט משימות · ot-task-manger

- מהות: Bot_TaskManger בטלגרם — הקלטה (faster-whisper מקומי) → משימות life.
- 2026-09-30: PLAN.md, תקציר/מייל, pytest voice+hybrid.
- הבא: pip install requirements-whisper.txt + smoke הקלטה.

<!-- project:openclaw_hub -->
## מנהל עבודה OpenClaw · `openclaw_hub`

- שלב: דשבורד :8788; תת-תחום engineering ב-form939-agent-hub/engineering/
- הבא: ענף project/system-engineering; openclaw_hub/engineering/NEXT_STEPS.md; career-hunt
- נתיב: `C:\Users\noam1\Documents\principal-architect-hub`
<!-- /project:openclaw_hub -->

<!-- project:openclaw_shell -->
## מעטפת OpenClaw (חלון Cursor) · `openclaw_shell`

- שלב: אזור Cursor; כלים ב-openclaw_hub/engineering
- הבא: project/system-engineering; openclaw_shell/NEXT_STEPS.md
- נתיב: `C:\Users\noam1\Documents\form939-agent-hub`
<!-- /project:openclaw_shell -->

<!-- project:life_widget -->
## ווידג'ט משימות · `life_widget`

- שלב: משימות אישיות בטלגרם ובווידג'ט. לא יוזמה A.
- הבא: שיפור רק אם יש משפט שימושי חסר.
- נתיב: `C:\Users\noam1\Documents\principal-architect-hub`
<!-- /project:life_widget -->

<!-- project:form_autofill -->
## מילוי טפסים · `form_autofill`

- שלב: זיהוי קובץ סינתטי נעשה. ראיון שדות.
- הבא: המשך ראיון שדות על docx דמה. בלי תיקיות משרד.
- נתיב: `C:\Users\noam1\Documents\form939-local-sandbox`
<!-- /project:form_autofill -->

<!-- project:hadash_gate -->
## שער סוג מסמך · `hadash_gate`

- שלב: סקירת ארכיטקט. מדידה על דמה.
- הבא: מדידה חוזרת על דמה. לא מממשים src משרד.
- נתיב: `C:\Users\noam1\Documents\form939-local-sandbox`
<!-- /project:hadash_gate -->

<!-- project:ds_portfolio -->
## תיק עבודות · `ds_portfolio`

- שלב: חמישה ריפו קטנים עלו ל-noam2177.
- הבא: שלב runnable לישיבה; בלי קורפוס משרד.
- נתיב: `C:\Users\noam1\Documents\GitHub\portfolio`
<!-- /project:ds_portfolio -->

<!-- project:he_segment -->
## פיצול תחיליות · `he_segment`

- שלב: מבחן קפוא 64/36/36.
- הבא: להגדיל רק train בלי לרדת מ-64, אחרי אישור תקציב.
- נתיב: `C:\Users\noam1\Documents\GitHub\he-segment`
<!-- /project:he_segment -->

<!-- project:he-rag -->
## he-rag · `he-rag`

- שלב: שליפה לקסיקלית + סירוב על דמה. לא LLM חי.
- הבא: טבלת eval במקום, בלי וקטורים עד בקשה.
- נתיב: `C:\Users\noam1\Documents\form939-local-sandbox\portfolio\he-rag`
<!-- /project:he-rag -->

<!-- project:sandbox-lab -->
## סנדבוקס מחקר · `sandbox-lab`

- שלב: מעבדה אישית. מחקר ו-benchmark סינתטי מותרים.
- הבא: יישור `glm_flash` / OpenCode עם GLM_API_BASE (סקירה 2026-10-03).
- משימות: `file_bus/projects/sandbox-lab/NEXT_STEPS.md`
- נתיב: `C:\Users\noam1\Documents\form939-local-sandbox`
<!-- /project:sandbox-lab -->

<!-- project:coc-tournament -->
## טורניר Clash · `coc-tournament`

- שלב: אתר הרשמה, ברקט, וצ'ק-אין.
- הבא: רק אם יש חיכוך במסך ציבורי.
- נתיב: `C:\Users\noam1\Documents\GitHub\coc-tournament`
<!-- /project:coc-tournament -->

<!-- project:coclz-connect -->
## CoCLZ · `coclz-connect`

- שלב: שיתוף בסיסים וצבאות.
- הבא: נפרד מהטורניר.
- נתיב: `C:\Users\noam1\Documents\GitHub\coclz-connect`
<!-- /project:coclz-connect -->

<!-- project:job-board -->
## job-board · `job-board`

- שלב: עמוד HTML מדוגמה מומצאת.
- הבא: בלי לוח משרות אמיתי.
- נתיב: `C:\Users\noam1\Documents\GitHub\job-board`
<!-- /project:job-board -->

<!-- project:fitness-tracker -->
## אתר מעקב כושר · `fitness-tracker`

- שלב: רשום ברשימת ההמשך. אין תיקייה מקומית במחשב הזה.
- הבא: לשלוח נתיב האתר או ריפו GitHub, ואז שינוי ראשון בטלגרם עם אשר שינוי.
- נתיב: ``
<!-- /project:fitness-tracker -->

<!-- project:virtual-closet -->
## ארון וירטואלי (Virtual Closet) · `virtual-closet`

- שלב: MVP v0: PWA React — ארון, גוף, overlay, share (local IndexedDB)
- הבא: בדיקת UX עם עומר; אחר כך v1: חיפוש NL + הצעות AI
- נתיב: `C:\Users\noam1\Documents\GitHub\virtual-closet`
<!-- /project:virtual-closet -->

<!-- project:presentation-builder -->
## Presentation Builder 3.0 · `presentation-builder`

- שלב: Vite+React רץ מקומית. צ'אט, קנבס 16:9, הצעות JSON, ייצוא PDF/PPTX.
- הבא: מפתח GLM מיושר (אחרי openclaw_shell/openclaw_hub); `npm run dev`.
- משימות: `file_bus/projects/presentation-builder/NEXT_STEPS.md`
- נתיב: `C:\Users\noam1\Documents\form939-agent-hub\presentation-builder`
<!-- /project:presentation-builder -->

<!-- project:system-engineering -->
## הנדסת מערכת (מאוחד) · `system-engineering`

- שלב: מאוחד ל-openclaw_hub/engineering — לא project_id פעיל
- הבא: ARCHIVED: file_bus/projects/system-engineering/ARCHIVED.md
- נתיב: `C:\Users\noam1\Documents\form939-agent-hub\engineering`
<!-- /project:system-engineering -->
