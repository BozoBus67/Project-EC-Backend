from fastapi import HTTPException

from db.client import supabase

# Both helpers return the new balance after the mutation, so callers that need
# it (e.g. /spin returning tokens_remaining to the frontend) don't have to do a
# second select round-trip. Mirrors services/cookies.py.

def add_tokens(user_uuid: str, amount: int) -> int:
  user = supabase.table("User_Login_Data").select("premium_game_data").eq("id", user_uuid).single().execute().data
  pgd = user["premium_game_data"]
  pgd["tokens"] = pgd["tokens"] + amount
  supabase.table("User_Login_Data").update({"premium_game_data": pgd}).eq("id", user_uuid).execute()
  return pgd["tokens"]

def spend_tokens(user_uuid: str, amount: int) -> int:
  user = supabase.table("User_Login_Data").select("premium_game_data").eq("id", user_uuid).single().execute().data
  pgd = user["premium_game_data"]
  if pgd["tokens"] < amount:
    raise HTTPException(status_code=400, detail="Not enough tokens")
  pgd["tokens"] = pgd["tokens"] - amount
  supabase.table("User_Login_Data").update({"premium_game_data": pgd}).eq("id", user_uuid).execute()
  return pgd["tokens"]
