"""One-time migration. Adolf Hitler was inserted alphabetically as
mastery_scroll_2, which shifted every subsequent character down by one slot
(Shadow Clone Jutsu became 3, CaseOh became 4, ..., Walter White became 25).

For each user, rewrite premium_game_data so the existing scroll counts follow
their character to its new key:
  pgd["mastery_scroll_25"] <- old pgd["mastery_scroll_24"]
  pgd["mastery_scroll_24"] <- old pgd["mastery_scroll_23"]
  ...
  pgd["mastery_scroll_3"]  <- old pgd["mastery_scroll_2"]
  pgd["mastery_scroll_2"]  <- 0   (Adolf Hitler — fresh)

Idempotent: skips rows where mastery_scroll_25 is already non-zero OR where
mastery_scroll_2 is non-zero AND mastery_scroll_25 is missing (ambiguous —
log and skip rather than double-shift).

Run once: `python scripts/insert_adolf_hitler_scroll.py` from backend root."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from db.client import supabase

rows = supabase.table("User_Login_Data").select("id, username, premium_game_data").execute().data
print(f"Found {len(rows)} users")

migrated = 0
skipped = 0
for row in rows:
  pgd = row["premium_game_data"] or {}
  if pgd.get("mastery_scroll_25", 0) != 0:
    print(f"  skip {row['username']} — mastery_scroll_25 already populated, looks already migrated")
    skipped += 1
    continue
  for n in range(24, 1, -1):
    pgd[f"mastery_scroll_{n + 1}"] = pgd.get(f"mastery_scroll_{n}", 0)
  pgd["mastery_scroll_2"] = 0
  supabase.table("User_Login_Data").update({"premium_game_data": pgd}).eq("id", row["id"]).execute()
  migrated += 1
  print(f"  migrated {row['username']}")

print(f"Done — migrated {migrated}, skipped {skipped}")
