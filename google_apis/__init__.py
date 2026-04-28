import json
import os
import base64
import logging
from datetime import datetime, timedelta
from typing import List, Optional

log = logging.getLogger("google_apis")

# Google API import (ixtiyoriy, agar o'rnatilgan bo'lsa)
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    log.warning("Google API kutubxonalari o'rnatilmagan. `pip install google-api-python-client google-auth`")

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive",
]

class GoogleAPI:
    def __init__(self):
        self.creds: Optional[object] = None
        self._calendar = None
        self._gmail = None
        self._drive = None

    def is_available(self) -> bool:
        return GOOGLE_AVAILABLE

    def _load_creds(self):
        if not GOOGLE_AVAILABLE:
            return False

        from config import cfg

        # Token JSON dan yuklash
        token_json = cfg.GOOGLE_TOKEN_JSON
        if token_json and os.path.exists(token_json):
            self.creds = Credentials.from_authorized_user_file(token_json, SCOPES)
        elif token_json:
            try:
                data = json.loads(token_json)
                self.creds = Credentials.from_authorized_user_info(data, SCOPES)
            except:
                pass

        if not self.creds:
            return False

        if self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())

        return self.creds.valid

    def _get_calendar(self):
        if not self._calendar:
            if not self._load_creds():
                raise RuntimeError("Google autentifikatsiya qilinmagan!")
            self._calendar = build("calendar", "v3", credentials=self.creds)
        return self._calendar

    def _get_gmail(self):
        if not self._gmail:
            if not self._load_creds():
                raise RuntimeError("Google autentifikatsiya qilinmagan!")
            self._gmail = build("gmail", "v1", credentials=self.creds)
        return self._gmail

    def _get_drive(self):
        if not self._drive:
            if not self._load_creds():
                raise RuntimeError("Google autentifikatsiya qilinmagan!")
            self._drive = build("drive", "v3", credentials=self.creds)
        return self._drive

    # ─── CALENDAR ───────────────────────────────────────────

    def get_events(self, day_offset: int = 0, max_results: int = 10) -> List[dict]:
        from config import cfg
        cal = self._get_calendar()

        target = datetime.now() + timedelta(days=day_offset)
        start = target.replace(hour=0, minute=0, second=0).isoformat() + "Z"
        end = target.replace(hour=23, minute=59, second=59).isoformat() + "Z"

        result = cal.events().list(
            calendarId=cfg.GOOGLE_CALENDAR_ID,
            timeMin=start,
            timeMax=end,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = []
        for e in result.get("items", []):
            start_time = e["start"].get("dateTime", e["start"].get("date", ""))
            events.append({
                "id": e["id"],
                "title": e.get("summary", "(sarlavsiz)"),
                "start": start_time[:16].replace("T", " "),
                "location": e.get("location", ""),
                "description": e.get("description", "")[:100],
            })
        return events

    def add_event(self, title: str, start_time: str, duration_minutes: int = 60) -> dict:
        from config import cfg
        cal = self._get_calendar()

        start = datetime.strptime(start_time, "%H:%M").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )
        end = start + timedelta(minutes=duration_minutes)

        event = {
            "summary": title,
            "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Tashkent"},
            "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Tashkent"},
        }
        created = cal.events().insert(calendarId=cfg.GOOGLE_CALENDAR_ID, body=event).execute()
        return {"id": created["id"], "title": title, "start": start.strftime("%H:%M")}

    # ─── GMAIL ───────────────────────────────────────────────

    def get_emails(self, max_results: int = 10) -> List[dict]:
        gmail = self._get_gmail()
        messages = gmail.users().messages().list(
            userId="me", maxResults=max_results, labelIds=["INBOX"]
        ).execute().get("messages", [])

        emails = []
        for m in messages:
            msg = gmail.users().messages().get(userId="me", id=m["id"], format="metadata",
                                                metadataHeaders=["From", "Subject", "Date"]).execute()
            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            emails.append({
                "id": m["id"],
                "from": headers.get("From", "—")[:50],
                "subject": headers.get("Subject", "(mavzusiz)")[:80],
                "date": headers.get("Date", "")[:25],
                "snippet": msg.get("snippet", "")[:100],
            })
        return emails

    def send_email(self, to: str, subject: str, body: str) -> bool:
        from email.mime.text import MIMEText
        gmail = self._get_gmail()

        msg = MIMEText(body)
        msg["to"] = to
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True

    # ─── DRIVE ───────────────────────────────────────────────

    def search_files(self, name: str, max_results: int = 10) -> List[dict]:
        drive = self._get_drive()
        results = drive.files().list(
            q=f"name contains '{name}' and trashed=false",
            pageSize=max_results,
            fields="files(id, name, mimeType, size, modifiedTime, webViewLink)"
        ).execute()

        files = []
        for f in results.get("files", []):
            size = int(f.get("size", 0))
            size_str = f"{size // 1024}KB" if size > 0 else "—"
            files.append({
                "id": f["id"],
                "name": f["name"],
                "type": f.get("mimeType", ""),
                "size": size_str,
                "modified": f.get("modifiedTime", "")[:10],
                "link": f.get("webViewLink", ""),
            })
        return files

    def upload_file(self, file_path: str, folder_id: str = None) -> dict:
        drive = self._get_drive()
        file_name = os.path.basename(file_path)
        metadata = {"name": file_name}
        if folder_id:
            metadata["parents"] = [folder_id]

        media = MediaFileUpload(file_path, resumable=True)
        uploaded = drive.files().create(
            body=metadata, media_body=media, fields="id, name, webViewLink"
        ).execute()
        return {
            "id": uploaded["id"],
            "name": uploaded["name"],
            "link": uploaded.get("webViewLink", ""),
        }


# Global instance
google_api = GoogleAPI()
