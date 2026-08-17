# FreshFlow B2B Ordering Platform

מערכת הזמנות B2B עבור FreshFlow, הנבנית כפרויקט Full-Stack מודולרי.

## מבנה הפרויקט

```text
freshflow-b2b-ordering-platform/
├── admin/                 # אפליקציית הניהול (בהמשך)
├── client/                # אפליקציית הלקוח (בהמשך)
├── db/                    # סכימת MySQL ונתוני פיתוח
├── docs/                  # תיעוד ארכיטקטורה ו-ERD
├── server/                # FastAPI Backend
├── .env.example           # דוגמה למשתני סביבה
├── .gitignore
├── docker-compose.yml     # MySQL לפיתוח מקומי
└── README.md
```

## הפעלת סביבת הפיתוח

### 1. יצירת קובץ הגדרות

העתק את `.env.example` לקובץ בשם `.env` ועדכן סיסמאות לפי הצורך.

### 2. הפעלת MySQL

```bash
docker compose up -d db
```

### 3. יצירת סביבה וירטואלית והתקנת Backend

```bash
cd server
python -m venv .venv
```

ב-Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. יצירת טבלאות באמצעות Alembic

מתוך `server/`:

```bash
alembic upgrade head
alembic current
```

לאחר שינוי במודלי SQLAlchemy יוצרים migration חדש ובודקים אותו ידנית:

```bash
alembic revision --autogenerate -m "describe the schema change"
```

### 5. הפעלת FastAPI

מתוך `server/`:

```bash
uvicorn app.main:app --reload
```

כתובות שימושיות:

- API: `http://127.0.0.1:8000`
- בדיקת תקינות: `http://127.0.0.1:8000/api/v1/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

## מצב נוכחי

- סכימת MySQL ונתוני Seed
- ERD מתועד
- שלד FastAPI
- שמונה מודלי SQLAlchemy
- Alembic ו־migration ראשוני
- הגדרות מבוססות משתני סביבה
- נתיב Health Check

Authentication והלוגיקה העסקית יתווספו בשלבים הבאים.

מרגע זה Alembic הוא מקור האמת לשינויים מבניים במסד. הקבצים תחת `db/`
נשארים כתיעוד של הסכימה וכמקור לנתוני פיתוח, אך Docker אינו מריץ אותם
אוטומטית כדי למנוע התנגשות עם migrations.
