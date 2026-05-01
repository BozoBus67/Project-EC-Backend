"""Proxy for the YouTube Data API v3 playlistItems endpoint.

Why proxy at all: the YouTube API key is a secret (not technically high-impact,
but it's quota-bound to our Google Cloud project, so leaking it lets randos
burn our 10k/day quota). We keep it server-side and expose only the playlist
output to the frontend.

The playlist refreshes from YouTube every 5 minutes — quick enough that a
song added to the playlist on youtube.com appears in the app shortly, slow
enough that a hot reload loop doesn't burn quota."""

import os
import time

from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter()

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
YOUTUBE_PLAYLIST_ID = os.environ.get("YOUTUBE_PLAYLIST_ID", "").strip()
if not YOUTUBE_API_KEY:
  raise RuntimeError("YOUTUBE_API_KEY env var is required (set it in backend/.env or Render dashboard)")
if not YOUTUBE_PLAYLIST_ID:
  raise RuntimeError("YOUTUBE_PLAYLIST_ID env var is required (set it in backend/.env or Render dashboard)")

CACHE_TTL_SECONDS = 5 * 60

_cache: dict = {"fetched_at": 0.0, "entries": []}


@router.get("/youtube_playlist")
async def get_youtube_playlist():
  now = time.time()
  if now - _cache["fetched_at"] < CACHE_TTL_SECONDS and _cache["entries"]:
    return _cache["entries"]

  entries: list[dict] = []
  page_token: str | None = None
  async with httpx.AsyncClient(timeout=10.0) as client:
    while True:
      params = {
        "part": "snippet",
        "playlistId": YOUTUBE_PLAYLIST_ID,
        "maxResults": 50,
        "key": YOUTUBE_API_KEY,
      }
      if page_token:
        params["pageToken"] = page_token
      res = await client.get("https://www.googleapis.com/youtube/v3/playlistItems", params=params)
      if res.status_code != 200:
        # Surface the YouTube API's own error message (quota exceeded, bad
        # playlist id, etc.) instead of a generic 500.
        detail = f"YouTube API returned {res.status_code}: {res.text[:300]}"
        raise HTTPException(status_code=502, detail=detail)
      payload = res.json()
      for item in payload.get("items", []):
        snippet = item["snippet"]
        # `videoOwnerChannelTitle` is missing for deleted/private videos. We
        # skip those — `resourceId.videoId` will still be there but the
        # video can't be played, so it's not a useful list entry.
        if "videoOwnerChannelTitle" not in snippet:
          continue
        entries.append({
          "video_id": snippet["resourceId"]["videoId"],
          "title": snippet["title"],
        })
      page_token = payload.get("nextPageToken")
      if not page_token:
        break

  _cache["fetched_at"] = now
  _cache["entries"] = entries
  return entries
