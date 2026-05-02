"""One-time migration. Renames every user's mastery-scroll keys from the old
positional `mastery_scroll_N` form to stable slug IDs (e.g. `charlie_kirk`,
`walter_white`). Also rewrites `chess_beaten_bots` entries from numeric IDs
to slugs.

The mapping below assumes the *post-Adolf-Hitler-shift* numbering — i.e. the
state of the codebase between commits eb7bfb9 (backend) and the slug refactor.
If a user's pgd was never run through `insert_adolf_hitler_scroll.py` (now
deleted), their counts will end up attributed to the next character down the
alphabet (Walter White count → Tun Tun Tun Sahur, etc.). Acceptable: the
project is pre-launch and the only player explicitly opted in to data drift.

Idempotent: the very first slug key (`6_7_kid`) is checked. If it's already
present in pgd, the row is assumed already migrated and skipped.

Run once: `python scripts/migrate_scrolls_to_slugs.py` from backend root."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from db.client import supabase

# OLD positional id  →  NEW slug id. Order matches the post-shift numbering
# (Adolf Hitler at position 2). Slugs match image-asset filename basenames.
OLD_TO_SLUG = {
  "mastery_scroll_1":  "6_7_kid",
  "mastery_scroll_2":  "adolf_hitler",
  "mastery_scroll_3":  "blurry_epstein",
  "mastery_scroll_4":  "caseoh",
  "mastery_scroll_5":  "charlie_kirk",
  "mastery_scroll_6":  "dexter",
  "mastery_scroll_7":  "diddy",
  "mastery_scroll_8":  "doakes",
  "mastery_scroll_9":  "donald_trump",
  "mastery_scroll_10": "drake",
  "mastery_scroll_11": "elon_musk",
  "mastery_scroll_12": "freddy_fazbear",
  "mastery_scroll_13": "george_floyd",
  "mastery_scroll_14": "hillary_clinton",
  "mastery_scroll_15": "ishowspeed",
  "mastery_scroll_16": "kai_cenat",
  "mastery_scroll_17": "khaby_lame",
  "mastery_scroll_18": "mark_zuckerberg",
  "mastery_scroll_19": "mr_beast",
  "mastery_scroll_20": "ninja_from_fortnite",
  "mastery_scroll_21": "roy_lee",
  "mastery_scroll_22": "state_trooper_cop",
  "mastery_scroll_23": "stephen_hawking",
  "mastery_scroll_24": "tun_tun_tun_sahur",
  "mastery_scroll_25": "walter_white",
}

rows = supabase.table("User_Login_Data").select("id, username, premium_game_data").execute().data
print(f"Found {len(rows)} users")

migrated = 0
skipped = 0
for row in rows:
  pgd = row["premium_game_data"] or {}
  if "6_7_kid" in pgd:
    print(f"  skip {row['username']} — slug keys already present")
    skipped += 1
    continue

  for old_key, slug in OLD_TO_SLUG.items():
    pgd[slug] = pgd.pop(old_key, 0)

  beaten = pgd.get("chess_beaten_bots") or []
  pgd["chess_beaten_bots"] = [OLD_TO_SLUG.get(b, b) for b in beaten]

  supabase.table("User_Login_Data").update({"premium_game_data": pgd}).eq("id", row["id"]).execute()
  migrated += 1
  print(f"  migrated {row['username']}")

print(f"Done — migrated {migrated}, skipped {skipped}")
