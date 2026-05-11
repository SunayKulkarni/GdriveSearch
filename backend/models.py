from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""
    history: list[dict] = []


class FileResult(BaseModel):
    id: str
    name: str
    mimeType: str
    mimeTypeLabel: str
    modifiedTime: str
    webViewLink: str
    size: str = "N/A"


class ChatResponse(BaseModel):
    response: str
    files: list[FileResult] = []
    session_id: str
