"""
Google Docs integration for CEO Brief.

Fetches recent documents from Google Drive and extracts content.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    Credentials = None

# Scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/documents.readonly'
]

# Paths
BASE_DIR = Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def authenticate() -> Optional[Credentials]:
    """
    Handle Google OAuth2 authentication.

    First time: Opens browser for consent.
    After: Uses saved token.
    """
    if Credentials is None:
        return None

    creds = None

    # Load existing token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # Refresh or get new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"Missing {CREDENTIALS_FILE}")
                print("Download from Google Cloud Console → APIs → Credentials")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for next time
        TOKEN_FILE.write_text(creds.to_json())

    return creds


def get_google_docs(days: int = 7, max_docs: int = 20) -> dict:
    """
    Fetch recent Google Docs.

    Args:
        days: How far back to look
        max_docs: Maximum documents to return

    Returns:
        Dict with documents list and summary
    """
    if Credentials is None:
        return {
            "error": "Google API libraries not installed",
            "documents": [],
            "summary": ""
        }

    creds = authenticate()
    if not creds:
        return {
            "error": "Not authenticated with Google",
            "documents": [],
            "summary": ""
        }

    try:
        # Build services
        drive_service = build('drive', 'v3', credentials=creds)
        docs_service = build('docs', 'v1', credentials=creds)

        # Calculate date cutoff
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'

        # Query for recent Google Docs
        query = (
            f"mimeType='application/vnd.google-apps.document' "
            f"and modifiedTime > '{cutoff}' "
            f"and trashed=false"
        )

        results = drive_service.files().list(
            q=query,
            pageSize=max_docs,
            fields="files(id, name, modifiedTime, owners)",
            orderBy="modifiedTime desc"
        ).execute()

        files = results.get('files', [])
        documents = []

        for file in files:
            doc_id = file['id']
            modified = file.get('modifiedTime', '')

            # Parse modification time
            try:
                mtime = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                days_ago = (datetime.now(mtime.tzinfo) - mtime).days
                modified_str = mtime.strftime("%Y-%m-%d")
            except:
                days_ago = 0
                modified_str = modified[:10]

            # Get document content preview
            preview = get_doc_preview(docs_service, doc_id)

            documents.append({
                "name": file['name'],
                "id": doc_id,
                "url": f"https://docs.google.com/document/d/{doc_id}",
                "modified": modified_str,
                "days_ago": days_ago,
                "preview": preview[:500] if preview else ""
            })

        summary = build_summary(documents)

        return {
            "documents": documents,
            "summary": summary,
            "count": len(documents)
        }

    except Exception as e:
        return {
            "error": str(e),
            "documents": [],
            "summary": ""
        }


def get_doc_preview(docs_service, doc_id: str, max_chars: int = 500) -> str:
    """Extract text preview from a Google Doc."""
    try:
        doc = docs_service.documents().get(documentId=doc_id).execute()
        content = doc.get('body', {}).get('content', [])

        text_parts = []
        char_count = 0

        for element in content:
            if 'paragraph' in element:
                for para_element in element['paragraph'].get('elements', []):
                    if 'textRun' in para_element:
                        text = para_element['textRun'].get('content', '')
                        text_parts.append(text)
                        char_count += len(text)
                        if char_count >= max_chars:
                            break
            if char_count >= max_chars:
                break

        return ''.join(text_parts)[:max_chars]

    except Exception:
        return ""


def extract_document_status(preview: str) -> Optional[str]:
    """Try to detect document status from content."""
    preview_lower = preview.lower()

    status_keywords = {
        "draft": "DRAFT",
        "final": "FINAL",
        "in progress": "IN PROGRESS",
        "completed": "COMPLETED",
        "pending review": "PENDING REVIEW",
        "wip": "WORK IN PROGRESS",
        "todo": "HAS TODOs"
    }

    for keyword, status in status_keywords.items():
        if keyword in preview_lower:
            return status

    return None


def build_summary(documents: list) -> str:
    """Build human-readable summary."""
    if not documents:
        return "No recent Google Docs found."

    lines = [f"{len(documents)} Google Docs modified recently:"]

    for doc in documents[:10]:
        status = extract_document_status(doc.get("preview", ""))
        status_str = f" [{status}]" if status else ""
        days = doc["days_ago"]
        days_str = "today" if days == 0 else f"{days}d ago"

        lines.append(f"  - {doc['name']} ({days_str}){status_str}")

    if len(documents) > 10:
        lines.append(f"  - ... and {len(documents) - 10} more")

    return "\n".join(lines)


if __name__ == "__main__":
    # Test - will trigger auth flow first time
    result = get_google_docs(days=7)
    if result.get("error"):
        print(f"Error: {result['error']}")
    else:
        print(result["summary"])
