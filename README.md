# 🏥 HealthSense – Family Health Report Understanding App

> **India-focused • Healthcare-safe • Informational only**
> No diagnosis. No medical advice. No panic language.

---

## 📁 Project Structure

```
healthsense/
│
├── backend/
│   ├── __init__.py
│   ├── main.py          ← FastAPI app entry point
│   ├── database.py      ← SQLite initialisation
│   ├── models.py        ← Pydantic schemas
│   ├── auth.py          ← Register / Login (SHA-256 + salt)
│   └── routes.py        ← All API route handlers
│
├── frontend/
│   ├── __init__.py
│   └── app.py           ← Streamlit multi-page UI
│
├── ocr/
│   ├── __init__.py
│   └── ocr_engine.py    ← pytesseract + OpenCV preprocessing
│
├── parser/
│   ├── __init__.py
│   └── extract_tests.py ← Regex-based test result extraction + flagging
│
├── explain/
│   ├── __init__.py
│   └── explanation_engine.py  ← Safe, non-diagnostic explanations
│
├── data/
│   ├── sample_report.txt
│   ├── generate_sample_image.py
│   ├── healthsense.db   ← auto-created on first run
│   └── uploads/         ← auto-created on first run
│
├── requirements.txt
└── README.md
```

---

## ⚙️ System Requirements

| Software    | Version  |
|-------------|----------|
| Python      | 3.9+     |
| Tesseract   | 4.x / 5.x|

---

## 🚀 Setup Instructions

### Step 1 – Install Tesseract OCR

**Ubuntu / Debian / WSL:**
```bash
sudo apt update
sudo apt install -y tesseract-ocr
```

**macOS (Homebrew):**
```bash
brew install tesseract
```

**Windows:**
Download from https://github.com/UB-Mannheim/tesseract/wiki
Add install path to your system PATH.

Verify: `tesseract --version`

---

### Step 2 – Create Python virtual environment

```bash
cd healthsense
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

---

### Step 3 – Install Python dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4 – (Optional) Generate sample report image

```bash
python data/generate_sample_image.py
```

This creates `data/sample_report.png` which you can upload to test OCR.

---

### Step 5 – Start the FastAPI backend

```bash
uvicorn backend.main:app --reload --port 8000
```

You should see:
```
✅  HealthSense DB initialised.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Browse API docs: http://localhost:8000/docs

---

### Step 6 – Start the Streamlit frontend

Open a **second terminal** (same virtual env):

```bash
streamlit run frontend/app.py
```

Opens in browser at: http://localhost:8501

---

## 🔄 Data Flow

```
Login → Select Profile → Upload Image
     → OCR (pytesseract + OpenCV)
     → Regex Parser (extract test name / value / unit / range)
     → Flag Detection (LOW / NORMAL / HIGH)
     → Safe Explanation Engine
     → Save to SQLite
     → Dashboard / History View
```

---

## 🧪 Sample Test

### Register + Login
1. Open http://localhost:8501
2. Go to **Register** tab → create user `testuser` / `test123`
3. Login

### Add Profile
1. Sidebar → **Manage Profiles**
2. Add: Name=`Ramesh Kumar`, Relation=`Self`, Age=`42`

### Upload Report
1. Sidebar → **Upload Report**
2. Select profile: `Ramesh Kumar`
3. Upload `data/sample_report.png`
4. Click **Process Report**

### Expected Output

| Test Name         | Value  | Unit      | Range         | Flag   |
|-------------------|--------|-----------|---------------|--------|
| Haemoglobin (Hb)  | 10.2   | g/dL      | 13.0–17.0     | 🔴 HIGH |
| Total WBC Count   | 11500  | cells/cumm| 4000–11000    | 🔴 HIGH |
| Blood Glucose (F) | 105    | mg/dL     | 70–100        | 🔴 HIGH |
| Total Cholesterol | 210    | mg/dL     | < 200         | 🔴 HIGH |
| TSH               | 5.8    | uIU/mL    | 0.5–5.0       | 🔴 HIGH |
| Serum Creatinine  | 1.1    | mg/dL     | 0.6–1.2       | 🟢 NORMAL |

---

## ⚕️ Safety Disclaimer

HealthSense is designed with strict healthcare safety principles:

- ✅ Shows only factual comparisons to reference ranges
- ✅ Uses neutral, calm language
- ✅ Always displays the informational disclaimer
- ❌ Never provides a diagnosis
- ❌ Never recommends specific treatments
- ❌ Never uses alarming or panic-inducing language

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `TesseractNotFoundError` | Install Tesseract and ensure it's in PATH |
| `Cannot reach the backend` | Check `uvicorn backend.main:app` is running on port 8000 |
| No tests extracted | OCR quality too low; try a cleaner/higher-res image. Demo data is used as fallback. |
| `ModuleNotFoundError` | Ensure venv is activated and `pip install -r requirements.txt` was run |
| Port 8000 in use | `uvicorn backend.main:app --port 8001` and update `API` in `frontend/app.py` |
| Image too dark/blurry | Preprocessing is applied; very low quality images may still fail OCR |

---

## 🗄️ Database Schema

```sql
users       (id, username, password, created_at)
profiles    (id, user_id, name, relation, age, created_at)
reports     (id, profile_id, file_path, report_date, created_at)
test_results(id, report_id, test_name, value, unit,
             range_low, range_high, range_text, flag)
```

SQLite file is auto-created at `data/healthsense.db`.

---

## 📦 Tech Stack

| Layer         | Technology                     |
|---------------|-------------------------------|
| Backend API   | FastAPI + Uvicorn              |
| Frontend UI   | Streamlit                      |
| Database      | SQLite (via stdlib `sqlite3`)  |
| OCR           | pytesseract + Tesseract 4/5    |
| Image process | OpenCV (`cv2`)                 |
| Parsing       | Python `re` (regex)            |
| Auth          | SHA-256 + random salt (stdlib) |

---

*Built as an MVP demo. Not intended for production medical use.*
