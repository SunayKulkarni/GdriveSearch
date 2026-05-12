import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

creds = Credentials.from_service_account_file(
    "backend/credentials/gdrive-496017-a5defdbb83b2.json",
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
service = build("drive", "v3", credentials=creds)

# Test 1: list ALL files the service account can see
print("=== ALL FILES ===")
result = service.files().list(
    q="trashed = false",
    fields="files(id, name, mimeType)",
    pageSize=20
).execute()
for f in result.get("files", []):
    print(f["name"], "-", f["mimeType"])

# Test 2: list files inside the specific folder
print("\n=== FOLDER CONTENTS ===")
folder_id = "1qkx58doSeYrcLjHPDysJyVJ36PsSqqlt"
result2 = service.files().list(
    q=f"'{folder_id}' in parents and trashed = false",
    fields="files(id, name, mimeType)",
    pageSize=20,
    supportsAllDrives=True,
    includeItemsFromAllDrives=True
).execute()
for f in result2.get("files", []):
    print(f["name"], "-", f["mimeType"])