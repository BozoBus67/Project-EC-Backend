from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from initializations_and_declarations.db_initialization import supabase
from utils import migrate_game_data

router = APIRouter()

class LoginRequest(BaseModel):
  username_or_email: str
  password: str

@router.post("/login")
def login(body: LoginRequest):
  if "@" in body.username_or_email:
    email = body.username_or_email
  else:
    row = supabase.table("User_Login_Data").select("email").eq(
      "username", body.username_or_email
    ).execute()
    if not row.data:
      raise HTTPException(status_code=401, detail="Invalid credentials")
    email = row.data[0]["email"]

  try:
    auth_result = supabase.auth.sign_in_with_password({
      "email": email,
      "password": body.password,
    })
  except Exception:
    raise HTTPException(status_code=401, detail="Invalid credentials")

  user_id = auth_result.user.id
  jwt = auth_result.session.access_token

  result = supabase.table("User_Login_Data").select(
    "id, username, game_data, premium_game_data"
  ).eq("id", user_id).execute()

  if not result.data:
    raise HTTPException(status_code=404, detail="User data not found")

  user = result.data[0]
  user["game_data"] = migrate_game_data(user["game_data"])

  return {
    "status": "ok",
    "jwt": jwt,
    "user": user,
  }