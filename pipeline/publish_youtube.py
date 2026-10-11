"""YouTube Shorts upload with scheduled publishing (YouTube Data API v3).

One-time setup (publisher chat, see HANDOFF-PUBLISHER.md):
  1. Google Cloud project → enable "YouTube Data API v3" → OAuth consent screen (External, add the
     channel's Google account as a test user) → OAuth client ID (Desktop app) → download JSON to
     secrets/youtube-client-secret.json (git-ignored).
  2. pip install google-api-python-client google-auth-oauthlib
  3. First run opens a browser to authorise the channel; the token is cached in secrets/youtube-token.json.

Upload:  python3 -m pipeline youtube-upload episodes/<id>.yaml --publish-at 2026-10-21T18:00:00+03:00
Comment: python3 -m pipeline youtube-comment <video_id> --text "..."   (pin it in YouTube Studio)

Quota: 10,000 units/day by default; videos.insert costs 1,600, so at most six uploads a day
until Google grants an increase. Scheduling = privacyStatus private + publishAt (RFC 3339).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .config import ROOT, render_dir
from .spec import Episode

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
SECRETS = ROOT / "secrets"
CATEGORY_EDUCATION = "27"


def _service(client_secrets: Path | None = None, token: Path | None = None):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as e:  # pragma: no cover
        raise SystemExit("pip install google-api-python-client google-auth-oauthlib") from e
    client_secrets = client_secrets or SECRETS / "youtube-client-secret.json"
    token = token or SECRETS / "youtube-token.json"
    creds = None
    if token.exists():
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
            creds = flow.run_local_server(port=0)
        token.parent.mkdir(exist_ok=True)
        token.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def _rfc3339_utc(s: str) -> str:
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise SystemExit("--publish-at needs a timezone offset, e.g. 2026-10-21T18:00:00+03:00")
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def upload(ep: Episode, publish_at: str | None, privacy: str = "private", client_secrets: Path | None = None,
           token: Path | None = None) -> dict:
    from googleapiclient.http import MediaFileUpload

    pub = render_dir(ep.id) / "publish"
    video = pub / f"{ep.id}.mp4"
    meta_path = pub / "metadata.json"
    if not video.exists() or not meta_path.exists():
        raise SystemExit(f"no publish bundle for {ep.id}: run `pipeline bundle` first (it refuses without a passing review)")
    meta = json.loads(meta_path.read_text())["youtube"]
    status = {"privacyStatus": "private" if publish_at else privacy, "selfDeclaredMadeForKids": False,
              "containsSyntheticMedia": True}          # altered/synthetic content disclosure
    if publish_at:
        status["publishAt"] = _rfc3339_utc(publish_at)
    body = {"snippet": {"title": meta["title"][:100], "description": meta["description"][:5000],
                        "tags": meta["tags"][:30], "categoryId": CATEGORY_EDUCATION, "defaultLanguage": "en"},
            "status": status}
    yt = _service(client_secrets, token)
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    vid = resp["id"]
    result = {"video_id": vid, "url": f"https://youtube.com/shorts/{vid}", "publish_at": status.get("publishAt"), "privacy": status["privacyStatus"]}
    (pub / "youtube.json").write_text(json.dumps(result, indent=2))
    return result


def comment(video_id: str, text: str, client_secrets: Path | None = None, token: Path | None = None) -> str:
    yt = _service(client_secrets, token)
    resp = yt.commentThreads().insert(part="snippet", body={"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": text}}}}).execute()
    return resp["id"]
