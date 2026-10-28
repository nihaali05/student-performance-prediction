# AI-Based Student Performance Prediction and Early Warning System

A full-stack web application combining Machine Learning (Scikit-Learn, Random Forest, XGBoost), Explainable AI (SHAP feature contributions), automated Early Warning rule engines, and interactive analytics dashboards in a clean **White & Purple** responsive UI design.

Students and faculty can exchange department-scoped in-app messages from the notification bell. New faculty study materials, student uploads, intervention messages, and quiz submissions appear in the recipient's inbox, with live unread updates while the app is open.

---

## Quick Start Guide

### Prerequisites
- Python 3.9+
- Node.js 18+ and `npm`

---

## 1. Backend Setup & Launch (Flask REST API + ML Engine)

1. Open a terminal in the project directory:
   ```bash
   cd "Student Performance Prediction"
   ```

2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Train ML Models & Generate Dataset:
   ```bash
   python backend/ml/train.py
   ```

4. Start the Flask Backend Server:
   ```bash
   python backend/app.py
   ```
   > The backend API will start on **`http://127.0.0.1:5000`** and auto-seed initial database records.

### Configure the AI Study Assistant

The study assistant uses Google Gemini for general questions and follow-up conversation. Open [backend/.env](./backend/.env) and add your replacement key after `GEMINI_API_KEY=`:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=paste-your-new-gemini-api-key-here
```

The backend loads this file automatically at startup. Save it and restart Flask after changing the key. The real `backend/.env` file is ignored by Git; never commit or share it. A template is available in `backend/.env.example`.

Install the backend requirements if needed:

```powershell
python -m pip install -r backend\requirements.txt
```

Keep the API key private and do not commit it to the project. If the key is missing or Gemini is unavailable, the assistant displays an error instead of returning a made-up or document-only answer.

---

## 2. Frontend Setup & Launch (React + Vite + Tailwind CSS)

1. Open a second terminal window in the `frontend` folder:
   ```bash
   cd "Student Performance Prediction/frontend"
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the Frontend Development Server:
   ```bash
   npm run dev
   ```
   > The application will open on **`http://localhost:3000`**.

---

## Demo Login Credentials (One-Click Demo Buttons Available on Login Screen)

| Role | Email | Password | Access & Features |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@analytics.edu` | `admin123` | Institutional dashboard, faculty/student directory, department analytics, ML model retrain & metrics comparison. |
| **Faculty** | `prof.smith@analytics.edu` | `faculty123` | Class roster, individual SHAP XAI student profiles, attendance/marks entry, CSV upload, intervention manager, early warning alerts. |
| **Student** | `alex.jones@student.edu` | `student123` | Personal GPA & attendance history, predicted final score, interactive What-If simulator, smart recommendations. |

---

## Project Folder Structure

```text
Student Performance Prediction/
├── backend/
│   ├── app.py                 # Main Flask server entry point
│   ├── config.py              # Configuration & SQLite/MySQL settings
│   ├── database.py            # SQLAlchemy database models (14 tables)
│   ├── seed.py                # Database seed script
│   ├── ml/
│   │   ├── train.py           # ML training script (Linear Reg, Random Forest, XGBoost)
│   │   ├── predict.py         # Inference & SHAP explanation engine
│   │   └── data_loader.py     # Dataset generator
│   ├── routes/                # REST API endpoints (auth, students, faculty, predictions, etc.)
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/        # Navbar, Sidebar, StatCard, RiskBadge
│   │   ├── context/           # AuthContext (JWT & Role RBAC)
│   │   ├── pages/             # Admin, Faculty, and Student pages
│   │   └── services/          # Axios API wrappers
│   ├── vite.config.js
│   └── package.json
├── database/
│   ├── schema.sql             # MySQL schema script
│   └── seed.sql               # SQL seed script
└── dataset/
    └── student_performance.csv# Pre-generated ML dataset (1,200 rows)
```
