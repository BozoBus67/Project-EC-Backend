from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from data.game_data import INITIAL_GAME_DATA
from db.client import supabase
from services.auth import require_user

router = APIRouter()

class SaveGameDataRequest(BaseModel):
  game_data: dict

@router.post("/save_game_data")
def save_game_data(body: SaveGameDataRequest, user=Depends(require_user)):
  result = supabase.table("User_Login_Data").update({"game_data": body.game_data}).eq("id", user.id).execute()
  if not result.data:
    raise HTTPException(status_code=500, detail="Failed to save game data")
  return {"status": "ok"}

@router.post("/reset_game_data")
def reset_game_data(user=Depends(require_user)):
  result = supabase.table("User_Login_Data").update({"game_data": INITIAL_GAME_DATA}).eq("id", user.id).execute()
  if not result.data:
    raise HTTPException(status_code=500, detail="Failed to reset game data")
  return {"status": "ok", "game_data": INITIAL_GAME_DATA}
