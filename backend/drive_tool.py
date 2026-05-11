from __future__ import annotations

import logging
import os
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


class GoogleDriveSearchInput(BaseModel):
    query: str = Field(..., description="Google Drive search query")
    max_results: int = Field(10, ge=1, le=100, description="Maximum results")


class GoogleDriveSearchTool(BaseTool):
    name = "google_drive_search"
    description = "Search Google Drive files with a query and return formatted results."
    args_schema = GoogleDriveSearchInput

    def _run(self, query: str, max_results: int = 10) -> str:
        logger.info("Executing google_drive_search query=%s max_results=%s", query, max_results)
        try:
            service_account_path = os.getenv("SERVICE_ACCOUNT_PATH", "")
            if not service_account_path:
                _LAST_FILES.clear()
                return "Error: SERVICE_ACCOUNT_PATH is not set."
            if not os.path.exists(service_account_path):
                _LAST_FILES.clear()
                return f"Error: service account file not found at {service_account_path}."

            scopes = ["https://www.googleapis.com/auth/drive.readonly"]
            credentials = Credentials.from_service_account_file(
                service_account_path, scopes=scopes
            )
            service = build("drive", "v3", credentials=credentials, cache_discovery=False)

            fields = "files(id,name,mimeType,modifiedTime,webViewLink,size)"
            response = (
                service.files()
                .list(q=query, pageSize=max_results, fields=fields)
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
