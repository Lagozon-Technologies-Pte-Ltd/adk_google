import asyncio
import os
import base64
import logging
from email.mime.text import MIMEText
from pathlib import Path

from fastmcp import FastMCP

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ---------------- CONFIG ----------------

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

BASE_DIR = Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Gmail MCP Server 📧")

# ---------------- AUTH ----------------

def get_gmail_service():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE, SCOPES
        )
        creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)

def extract_body(payload):
    """
    Extracts the email body (prefers text/plain, falls back to text/html)
    """
    if "parts" not in payload:
        # Single-part message
        body = payload.get("body", {}).get("data")
        if body:
            return base64.urlsafe_b64decode(body).decode("utf-8", errors="ignore")
        return ""

    plain_text = None
    html_text = None

    for part in payload["parts"]:
        mime_type = part.get("mimeType")
        body_data = part.get("body", {}).get("data")

        if not body_data:
            continue

        decoded = base64.urlsafe_b64decode(body_data).decode(
            "utf-8", errors="ignore"
        )

        if mime_type == "text/plain":
            plain_text = decoded
        elif mime_type == "text/html":
            html_text = decoded

    return plain_text or html_text or ""


# ---------------- TOOLS ----------------

@mcp.tool()
def send_email(to: str, subject: str, body: str):
    """
    Send an email using Gmail.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text email body
    """
    service = get_gmail_service()

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw},
    ).execute()

    return {
        "status": "sent",
        "to": to,
        "subject": subject,
    }

@mcp.tool()
def read_recent_emails(max_results: int = 5):
    """
    Read recent emails including body content.
    """
    service = get_gmail_service()

    results = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        labelIds=["INBOX"],
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full",
        ).execute()

        headers = {
            h["name"]: h["value"]
            for h in data["payload"]["headers"]
        }

        body = extract_body(data["payload"])

        emails.append({
            "from": headers.get("From"),
            "subject": headers.get("Subject"),
            "date": headers.get("Date"),
            "body": body,
            "id": msg["id"],
        })

    return emails

# ---------------- RUN ----------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    logger.info(f"🚀 Gmail MCP running on port {port}")

    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=port,
        )
    )
