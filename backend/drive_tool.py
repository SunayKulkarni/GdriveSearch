from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_LAST_FILES: list[dict[str, Any]] = []


def get_raw_files() -> list[dict[str, Any]]:
    return list(_LAST_FILES)


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


def _resolve_service_account_path(path_value: str) -> str:
    if not path_value:
        return ""

    raw_path = Path(path_value)
    if raw_path.is_absolute():
        return str(raw_path) if raw_path.exists() else ""

    backend_dir = Path(__file__).resolve().parent
    repo_root = backend_dir.parent
    candidates = [
        Path(path_value),
        backend_dir / path_value,
        repo_root / path_value,
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return ""


def _normalize_query(query: str) -> str:
    normalized = query.strip()
    if not normalized:
        return normalized

    normalized = re.sub(
        r"mimeType\s*=\s*['\"]image/\*?['\"]",
        "mimeType contains 'image/'",
        normalized,
        flags=re.IGNORECASE,
    )

    if not re.search(r"\btrashed\s*=", normalized, flags=re.IGNORECASE):
        normalized = f"{normalized} and trashed = false"

    return normalized


def _apply_folder_scope(query: str, folder_id: str) -> str:
    if not folder_id:
        return query

    if re.search(r"\bin\s+parents\b", query, flags=re.IGNORECASE):
        return query

    if query:
        return f"{query} and '{folder_id}' in parents"
    return f"'{folder_id}' in parents"


class GoogleDriveSearchInput(BaseModel):
    query: str = Field(..., description="Google Drive search query")
    max_results: int = Field(10, ge=1, le=100, description="Maximum results")


class GoogleDriveSearchTool(BaseTool):
    name: str = "google_drive_search"
    description: str = "Search Google Drive files with a query and return formatted results."
    args_schema: type[GoogleDriveSearchInput] = GoogleDriveSearchInput

    def _run(self, query: str, max_results: int = 10) -> str:
        safe_max_results = max(10, min(max_results, 100))
        normalized_query = _normalize_query(query)
        folder_id = os.getenv("DRIVE_FOLDER_ID", "").strip()
        scoped_query = _apply_folder_scope(normalized_query, folder_id)
        logger.info(
            "Executing google_drive_search query=%s max_results=%s",
            scoped_query,
            safe_max_results,
        )
        try:
            service_account_path = (
                os.getenv("SERVICE_ACCOUNT_PATH", "")
                or os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
            )
            if not service_account_path:
                _LAST_FILES.clear()
                return "Error: SERVICE_ACCOUNT_PATH or GOOGLE_APPLICATION_CREDENTIALS is not set."

            resolved_path = _resolve_service_account_path(service_account_path)
            if not resolved_path:
                _LAST_FILES.clear()
                return f"Error: service account file not found at {service_account_path}."

            scopes = ["https://www.googleapis.com/auth/drive.readonly"]
            credentials = Credentials.from_service_account_file(
                resolved_path, scopes=scopes
            )
            service = build("drive", "v3", credentials=credentials, cache_discovery=False)

            fields = "files(id,name,mimeType,modifiedTime,webViewLink,size)"
            response = (
                service.files()
                .list(
                    q=scoped_query,
                    pageSize=safe_max_results,
                    fields=fields,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            files = response.get("files", [])
            _LAST_FILES[:] = files

            if not files:
                return "No files found."

            lines = [f"Found {len(files)} file(s):"]
            for item in files:
                name = item.get("name", "(no name)")
                mime_type = item.get("mimeType", "")
                label = _mime_type_label(mime_type)
                modified = item.get("modifiedTime", "")
                link = item.get("webViewLink", "")
                size = item.get("size", "N/A")
                lines.append(
                    f"- {name} ({label}) | modified: {modified} | size: {size} | link: {link}"
                )

            return "\n".join(lines)
        except Exception as exc:
            _LAST_FILES.clear()
            return f"Error: {exc}"
