from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from initialisations_and_declarations.db_initialization import supabase
from initialisations_and_declarations.premium_game_data_declarations import INITIAL_PREMIUM_GAME_DATA

router = APIRouter()

class SignUpRequest(BaseModel):
  email: str
  username: str
  password: str

@router.post("/signup")
def signup(body: SignUpRequest):
  try:
    supabase.table("User_Login_Data").insert({
      "email": body.email,
      "username": body.username,
      "password": body.password,
      "game_data": {},
      "premium_game_data": INITIAL_PREMIUM_GAME_DATA,
    }).execute()
  except Exception:
    raise HTTPException(status_code=400, detail="Username or email already taken")

  return {"status": "ok"}