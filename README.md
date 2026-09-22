# 🎯 Resume Intelligence: AI-Powered Applicant Tracking System

Welcome to **Resume Intelligence**, an advanced AI-powered Applicant Tracking System (ATS) designed to streamline the hiring process. This application automates the tedious task of reading and evaluating resumes by leveraging Natural Language Processing (NLP) and Machine Learning (ML) to extract skills, predict job domains, and calculate objective match scores against specific job requirements.

---

## 🌟 Key Features

1. **Intelligent PDF Processing:** Upload resumes in PDF format. The system automatically extracts raw text using `pdfminer`.
2. **NLP Skill Extraction:** Uses a customized `spaCy` NLP pipeline with a `PhraseMatcher` to identify hundreds of technical and soft skills (e.g., Python, Machine Learning, Agile) within the unstructured resume text.
3. **ML Domain Classification:** A trained Machine Learning classifier (using Scikit-Learn) analyzes the resume text and predicts the candidate's professional domain (e.g., Data Science, HR, Mechanical Engineering) with a confidence score.
4. **Automated Skill Matching:** Create job profiles with *Required* and *Preferred* skills. The system mathematically scores candidates based on their extracted skills and applies a bonus for domain alignment.
5. **Interactive Dashboard:** A rich `Streamlit` frontend provides a modern, responsive UI for HR admins to view analytics, manage job profiles, review candidate scores, and manage human-in-the-loop screening decisions.
6. **Secure Architecture:** JWT-based authentication system ensuring only authorized HR personnel and Administrators can access candidate data.

---

## 🛠️ Technology Stack

This project is built using a modern Python data stack, separating the backend intelligence from the frontend user interface.

### **Languages**
- **Python 3.12+**: The core language powering both the backend APIs and the frontend UI.
- **SQL**: Used via SQLAlchemy for database schema management and queries.

### **Backend (API & Intelligence)**
- **FastAPI**: A high-performance web framework used to build the RESTful API endpoints.
- **Uvicorn**: The ASGI web server used to run the FastAPI application.
- **SQLAlchemy**: The Object Relational Mapper (ORM) handling interactions with the SQLite database.
- **Pydantic**: Used for strict data validation and JSON serialization.
- **spaCy**: The core NLP library used for named entity recognition and skill matching (`en_core_web_sm` model).
- **Scikit-Learn**: Used for training and deploying the TF-IDF and LinearSVC based domain classification models.
- **pdfminer.six**: Used for extracting raw text from PDF documents.
- **Pytest**: Used for backend unit and integration testing.

### **Frontend (User Interface)**
- **Streamlit**: A rapid application framework used to build the interactive HR dashboard without writing raw HTML/JS/CSS.
- **Streamlit Components**: Used for rendering metrics, dataframes, and file upload widgets.

### **Dataset**
- **Source**: The models were trained and tested using publicly available Resume Datasets from **Kaggle** (specifically datasets containing categorizations like Data Science, HR, Sales, Arts, etc.). 
- **Content**: The training data (`train.csv` and `master_resumes.jsonl`) contains thousands of resumes that were pre-processed to extract text and labeled by domain to train the classifier.

---

## 📂 Project Structure

```text
RESUME_SCREENING/
│
├── backend/                  # The FastAPI Backend System
│   ├── app/
│   │   ├── api/v1/           # REST API Routes (auth, jobs, resumes, screening)
│   │   ├── models/           # SQLAlchemy Database Models
│   │   ├── schemas/          # Pydantic Validation Schemas
│   │   ├── services/         # Core Logic (NLP matching, PDF extraction, DB ops)
│   │   ├── main.py           # FastAPI Application Entrypoint
│   │   └── config.py         # Application Configuration & Environment Vars
│   └── tests/                # Pytest unit tests
│
├── frontend/                 # The Streamlit Frontend System
│   ├── app.py                # Main Streamlit Application Router
│   ├── views/                # Individual UI Pages (Dashboard, Upload, Jobs, Analytics)
│   ├── components/           # Reusable UI components (Sidebar)
│   └── services/             # API Client for communicating with the Backend
│
└── ml/                       # Machine Learning & AI Scripts
    ├── models/               # Saved ML models (.pkl or .joblib)
    ├── scripts/              # Training scripts, Batch processing, OCR extraction
    └── shared/               # Shared taxonomies (skill lists, label mappings)
```

---

## 🚀 How to Run the Application Locally

To test the application on your local machine, you will need to start both the backend API server and the frontend Streamlit dashboard.

### 1. Prerequisites
Ensure you have Python 3.10+ installed. It is highly recommended to use a virtual environment (`.venv`).

### 2. Install Dependencies
Install the required packages for the backend and download the spaCy NLP model:
```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

*(Note: The frontend has its own requirements, ensure Streamlit and Pandas are installed in your environment).*

### 3. Start the Backend API (FastAPI)
The backend must be running for the frontend to function. From the project root:
```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
*The API will be available at `http://127.0.0.1:8000`. You can view the interactive Swagger API documentation at `http://127.0.0.1:8000/docs`.*

### 4. Start the Frontend UI (Streamlit)
Open a **new terminal window** (keep the backend running) and start the frontend:
```bash
# From the project root
streamlit run frontend/app.py
```
*The Streamlit dashboard will automatically open in your browser at `http://localhost:8501`.*

---

## 🎯 How to Use the Application

1. **Login:** Access the frontend at `http://localhost:8501`. Log in using the default administrator credentials:
   - **Email:** `admin@example.com`
   - **Password:** `changeme123`
2. **Create a Job Profile:** Navigate to the **Jobs** tab. Create a new job (e.g., "Senior Data Scientist"). Add *Required* skills (e.g., Python, Machine Learning) and *Preferred* skills.
3. **Upload Candidates:** Go to the **Upload Resume** tab. Upload a PDF resume. The system will process it, extract the text, and classify the candidate's domain.
4. **Screening:** View the results. The system will automatically calculate a match score against the job profile you created. 
5. **Review Results:** Go to the **Screening Results** tab to see a ranked list of all candidates. Click on a candidate to see a detailed breakdown of exactly *why* they received their score, which skills were matched, and which required skills are missing. You can then officially "Approve" or "Reject" them.

---

## 🛡️ Ethical AI & Bias Mitigation
This application is strictly designed as a **decision-support tool** for human HR professionals, not a fully autonomous hiring system.
- The scoring algorithm is 100% transparent and deterministic (formula-based).
- Protected characteristics (age, gender, race, etc.) are entirely excluded from the scoring process.
- No automated rejection takes place; all candidate scores simply inform human review.

---
*Built with ❤️ for modern, intelligent recruitment.*
