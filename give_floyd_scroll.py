from dotenv import load_dotenv
load_dotenv()

from db.client import supabase

USERNAME = "user1"
SCROLL_ID = "mastery_scroll_12"  # George Floyd
AMOUNT = 1

row = supabase.table("User_Login_Data").select("id, premium_game_data").eq("username", USERNAME).single().execute().data
pgd = row["premium_game_data"]
pgd[SCROLL_ID] = pgd.get(SCROLL_ID, 0) + AMOUNT
supabase.table("User_Login_Data").update({"premium_game_data": pgd}).eq("id", row["id"]).execute()
print(f"Done — {USERNAME} now has {pgd[SCROLL_ID]}× {SCROLL_ID} (George Floyd)")
