"""
Local document scanner for CEO Brief.

Scans specified directories for Word documents and extracts status info.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

try:
    from docx import Document
except ImportError:
    Document = None


def scan_local_documents(
    directories: list[str],
    extensions: list[str] = [".docx", ".doc"],
    days: int = 7,
    max_preview_chars: int = 500,
    max_files: int = 50
) -> dict:
    """
    Scan directories for recent documents.

    Args:
        directories: List of directory paths to scan
        extensions: File extensions to look for
        days: Only include files modified in last N days
        max_preview_chars: Max chars to extract from each doc

    Returns:
        Dict with documents list and summary
    """
    if Document is None:
        return {
            "error": "python-docx not installed",
            "documents": [],
            "summary": ""
        }

    cutoff = datetime.now() - timedelta(days=days)
    documents = []
    files_checked = 0
    limit_reached = False

    for directory in directories:
        if limit_reached:
            break
        dir_path = Path(directory)
        if not dir_path.exists():
            continue

        for ext in extensions:
            if limit_reached:
                break
            for file_path in dir_path.rglob(f"*{ext}"):
                files_checked += 1
                if files_checked > max_files:
                    limit_reached = True
                    break
                try:
                    # Get modification time
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                    if mtime < cutoff:
                        continue

                    # Extract content preview for .docx
                    preview = ""
                    if ext == ".docx":
                        preview = extract_docx_preview(file_path, max_preview_chars)

                    documents.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "modified": mtime.strftime("%Y-%m-%d %H:%M"),
                        "days_ago": (datetime.now() - mtime).days,
                        "preview": preview
                    })
                except Exception as e:
                    continue

    # Sort by modification time (most recent first)
    documents.sort(key=lambda x: x["modified"], reverse=True)

    summary = build_summary(documents)

    return {
        "documents": documents,
        "summary": summary,
        "count": len(documents)
    }


def extract_docx_preview(file_path: Path, max_chars: int) -> str:
    """Extract first N characters from a docx file."""
    try:
        doc = Document(file_path)
        text_parts = []
        char_count = 0

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                text_parts.append(text)
                char_count += len(text)
                if char_count >= max_chars:
                    break

        preview = " ".join(text_parts)[:max_chars]
        return preview
    except Exception:
        return ""


def extract_document_status(preview: str) -> Optional[str]:
    """
    Try to detect document status from content.

    Looks for common status indicators like:
    - "Status: Draft"
    - "DRAFT"
    - "Version 1.0"
    - "FINAL"
    - "IN PROGRESS"
    """
    preview_lower = preview.lower()

    status_keywords = {
        "draft": "DRAFT",
        "final": "FINAL",
        "in progress": "IN PROGRESS",
        "completed": "COMPLETED",
        "pending review": "PENDING REVIEW",
        "wip": "WORK IN PROGRESS"
    }

    for keyword, status in status_keywords.items():
        if keyword in preview_lower:
            return status

    return None


def build_summary(documents: list) -> str:
    """Build human-readable summary of documents."""
    if not documents:
        return "No recent documents found."

    lines = [f"{len(documents)} documents modified in the last 7 days:"]

    for doc in documents[:10]:  # Limit to 10
        status = extract_document_status(doc.get("preview", ""))
        status_str = f" [{status}]" if status else ""
        days = doc["days_ago"]
        days_str = "today" if days == 0 else f"{days}d ago"

        lines.append(f"  - {doc['name']} ({days_str}){status_str}")

    if len(documents) > 10:
        lines.append(f"  - ... and {len(documents) - 10} more")

    return "\n".join(lines)


# Default directories to scan (customize these)
DEFAULT_DIRECTORIES = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Downloads"),
]


if __name__ == "__main__":
    # Test
    result = scan_local_documents(DEFAULT_DIRECTORIES, days=7)
    print(result["summary"])
