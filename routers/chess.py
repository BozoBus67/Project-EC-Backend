from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from data.scrolls import MASTERY_SCROLLS
from db.client import supabase
from services.auth import require_user

router = APIRouter()

# A chess bot's id is either a scroll slug (e.g. "charlie_kirk") or the
# special "epstein" boss id. The naming is "bot_id" rather than "scroll_id"
# because the value isn't always a scroll — Epstein in particular isn't.
EPSTEIN_BOT_ID = "epstein"

# Slugs in MASTERY_SCROLLS that don't map to a chess bot. Mirror of the
# `chess_elo: null` flag in vite_part_react/src/shared/scroll_registry.js.
# Keep in sync with the frontend — the drift is small (one slug today) and
# enforced by the regular-bots gate below.
EXCLUDED_FROM_CHESS = {"blurry_epstein"}

REGULAR_BOT_SLUGS = set(MASTERY_SCROLLS.keys()) - EXCLUDED_FROM_CHESS
VALID_BOT_IDS = REGULAR_BOT_SLUGS | {EPSTEIN_BOT_ID}


class MarkBotBeatenRequest(BaseModel):
  bot_id: str


@router.post("/chess/mark_bot_beaten")
def mark_chess_bot_beaten(body: MarkBotBeatenRequest, user=Depends(require_user)):
  if body.bot_id not in VALID_BOT_IDS:
    raise HTTPException(status_code=400, detail=f"Unknown chess bot id '{body.bot_id}'")

  pgd = supabase.table("User_Login_Data").select("premium_game_data").eq("id", user.id).single().execute().data["premium_game_data"]
  beaten = pgd["chess_beaten_bots"]

  # Epstein is gated: must beat every regular bot first. Frontend already
  # enforces this visually, but a hand-crafted POST shouldn't be able to skip
  # the grind. Self-cheating prevention.
  if body.bot_id == EPSTEIN_BOT_ID and not REGULAR_BOT_SLUGS.issubset(beaten):
    missing = sorted(REGULAR_BOT_SLUGS - set(beaten))
    raise HTTPException(status_code=403, detail=f"Beat every regular bot before challenging Epstein. Still missing: {missing}")

  if body.bot_id not in beaten:
    beaten.append(body.bot_id)
    pgd["chess_beaten_bots"] = beaten
    supabase.table("User_Login_Data").update({"premium_game_data": pgd}).eq("id", user.id).execute()
  return {"chess_beaten_bots": pgd["chess_beaten_bots"]}
