from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

from backend.agent import run_agent
from backend.models import ChatRequest, ChatResponse, FileResult

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _mime_type_label(mime_type: str) -> str:
    if mime_type == "application/vnd.google-apps.document":
        return "Google Doc"
    if mime_type == "application/vnd.google-apps.spreadsheet":
        return "Google Sheet"
    if mime_type == "application/vnd.google-apps.presentation":
        return "Google Slides"
    if mime_type == "application/pdf":
        return "PDF"
    if mime_type.startswith("image/"):
        return "Image"
    return "File"


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    session_id = payload.session_id or str(uuid4())
    try:
        result = run_agent(payload.message, payload.history)
        raw_files = result.get("files", [])

        files: list[FileResult] = []
        for item in raw_files:
            mime_type = str(item.get("mimeType", ""))
            size_value = item.get("size")
            size = str(size_value) if size_value is not None else "N/A"
            files.append(
                FileResult(
                    id=str(item.get("id", "")),
                    name=str(item.get("name", "")),
                    mimeType=mime_type,
                    mimeTypeLabel=_mime_type_label(mime_type),
                    modifiedTime=str(item.get("modifiedTime", "")),
                    webViewLink=str(item.get("webViewLink", "")),
                    size=size,
                )
            )

        response_text = str(result.get("response", ""))
        return ChatResponse(response=response_text, files=files, session_id=session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def root() -> dict:
    return {"message": "Drive Agent API running"}
