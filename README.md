# 🗂️ Google Drive Agent

A conversational AI agent that helps you search, filter, and discover files in Google Drive using natural language. Built with FastAPI, LangGraph, and Streamlit.

---

## Demo

> "Find all PDF files" → returns matching files with links
> "Show spreadsheets modified this week" → filters by type and date
> "Search documents about marketing" → full-text search across Drive

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      User Browser                       │
│                  Streamlit Frontend                     │
│              (chat UI + file cards)                     │
└─────────────────────┬───────────────────────────────────┘
                      │  POST /chat
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                         │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │              LangGraph Agent                    │   │
│   │                                                 │   │
│   │   User message → LLM (Gemini/OpenAI/Groq)      │   │
│   │        ↓                                        │   │
│   │   Translates to Drive API query string          │   │
│   │        ↓                                        │   │
│   │   DriveSearchTool → Google Drive API            │   │
│   │        ↓                                        │   │
│   │   Returns file results + formatted response     │   │
│   └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                 Google Drive API                         │
│         (Service Account Authentication)                │
│    files.list() with q parameter for search             │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Frontend  | Streamlit                           |
| Backend   | FastAPI + Uvicorn                   |
| Agent     | LangGraph (ReAct pattern)           |
| LLM       | Gemini 1.5 Flash / OpenAI / Groq    |
| Drive API | Google Drive v3 (Service Account)   |

---

## Project Structure

```
gdrive-agent/
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, /chat endpoint
│   ├── agent.py         # LangGraph ReAct agent
│   ├── drive_tool.py    # Google Drive search tool
│   ├── models.py        # Pydantic schemas
│   ├── credentials/
│   │   └── service_account.json   # ← your service account (gitignored)
│   └── requirements.txt
├── frontend/
│   ├── app.py           # Streamlit chat UI
│   └── requirements.txt
├── .env                 # root-level env file (gitignored)
├── .gitignore
└── README.md
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/gdrive-agent.git
cd gdrive-agent
```

### 2. Set up Google Cloud

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project
3. Enable the **Google Drive API**:
   `APIs & Services → Library → Google Drive API → Enable`
4. Create a Service Account:
   `APIs & Services → Credentials → Create Credentials → Service Account`
5. Download the JSON key:
   `Click service account → Keys → Add Key → JSON`
6. Place it at `backend/credentials/service_account.json`

### 3. Share your Drive folder

1. Open your Google Drive folder
2. Click **Share**
3. Paste your service account email (found in the JSON under `client_email`)
4. Set role to **Viewer** → click **Share**

### 4. Get an LLM API key

| Provider | Get key at |
|----------|-----------|
| Gemini (recommended, free tier) | [aistudio.google.com](https://aistudio.google.com) |
| OpenAI | [platform.openai.com](https://platform.openai.com) |
| Groq (fast + free) | [console.groq.com](https://console.groq.com) |

### 5. Configure environment

Create a `.env` file at the project root:

```bash
# Choose one: gemini | openai | groq
LLM_PROVIDER=gemini

# Paste the key for your chosen provider
GOOGLE_API_KEY=your_gemini_key_here
OPENAI_API_KEY=
GROQ_API_KEY=

# Google Drive
SERVICE_ACCOUNT_PATH=credentials/service_account.json
DRIVE_FOLDER_ID=your_google_drive_folder_id_here
```

To find your `DRIVE_FOLDER_ID`, open the folder in Drive and copy the ID from the URL:
```
https://drive.google.com/drive/folders/THIS_IS_YOUR_FOLDER_ID
```

### 6. Install dependencies

```bash
# Backend
pip install -r backend/requirements.txt

# Frontend
pip install -r frontend/requirements.txt
```

### 7. Run locally

```bash
# Terminal 1 — start backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — start frontend
cd frontend
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Verify Drive connection

Before running the full app, test your Drive connection:

```python
# test_drive.py
from dotenv import load_dotenv
load_dotenv()

import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_service_account_file(
    "backend/credentials/service_account.json",
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
service = build("drive", "v3", credentials=creds)

folder_id = os.getenv("DRIVE_FOLDER_ID")
result = service.files().list(
    q=f"'{folder_id}' in parents and trashed = false",
    fields="files(id, name, mimeType)",
    supportsAllDrives=True,
    includeItemsFromAllDrives=True
).execute()

for f in result.get("files", []):
    print(f["name"], "-", f["mimeType"])
```

```bash
python test_drive.py
```

You should see your Drive files listed in the terminal.

---

## Example Queries

| What you type | What the agent searches |
|---------------|------------------------|
| Find all PDFs | `mimeType = 'application/pdf' and trashed = false` |
| Show Google Sheets | `mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false` |
| Find files named report | `name contains 'report' and trashed = false` |
| Search docs about budget | `fullText contains 'budget' and trashed = false` |
| Find images | `mimeType contains 'image/' and trashed = false` |
| Files modified this week | `modifiedTime > '2024-12-05T00:00:00' and trashed = false` |

---

## Deployment

### Backend → Railway

1. Push your code to GitHub (make sure `credentials/` and `.env` are in `.gitignore`)
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables in Railway dashboard (same as your `.env`)
4. Add your `service_account.json` contents as a `SERVICE_ACCOUNT_JSON` env var and update `drive_tool.py` to parse it from env instead of file
5. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Frontend → Streamlit Cloud

1. Push `frontend/app.py` and `frontend/requirements.txt` to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Point to `frontend/app.py`
4. Add `BACKEND_URL=https://your-railway-app.railway.app` in Streamlit secrets

---

## .gitignore

```
backend/credentials/
.env
__pycache__/
*.pyc
.DS_Store
*.egg-info/
dist/
```

---

## API Reference

### `POST /chat`

```json
Request:
{
  "message": "find all PDF files",
  "session_id": "optional-uuid",
  "history": [
    {"role": "user", "content": "hi"},
    {"role": "assistant", "content": "Hello! How can I help?"}
  ]
}

Response:
{
  "response": "Found 4 files. Here's what I found:",
  "session_id": "uuid",
  "files": [
    {
      "id": "file_id",
      "name": "Daily Report.pdf",
      "mimeType": "application/pdf",
      "mimeTypeLabel": "PDF",
      "modifiedTime": "2024-12-10T08:30:00Z",
      "webViewLink": "https://drive.google.com/...",
      "size": "102400"
    }
  ]
}
```

### `GET /health`

```json
{ "status": "ok" }
```
