import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from db.client import supabase

USERNAME = "user1"
TOKENS = 9999

row = supabase.table("User_Login_Data").select("id, premium_game_data").eq("username", USERNAME).single().execute().data
pgd = row["premium_game_data"]
pgd["tokens"] = TOKENS
supabase.table("User_Login_Data").update({"premium_game_data": pgd}).eq("id", row["id"]).execute()
print(f"Done — {USERNAME} now has {TOKENS} tokens")
