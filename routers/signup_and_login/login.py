from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from initialisations_and_declarations.db_initialization import supabase

router = APIRouter()

class LoginRequest(BaseModel):
  username_or_email: str
  password: str

@router.post("/login")
def login(body: LoginRequest):
  result = supabase.table("User_Login_Data").select(
    "username, game_data, premium_game_data"
  ).or_(
    f"username.eq.{body.username_or_email},email.eq.{body.username_or_email}"
  ).eq("password", body.password).single().execute()

  if not result.data:
    raise HTTPException(status_code=401, detail="Invalid username or password")

  supabase.table("User_Login_Data").update({
    "last_login_time": datetime.now(timezone.utc).isoformat(),
  }).eq("username", result.data["username"]).execute()

  return {"status": "ok", "username": result.data["username"]}
