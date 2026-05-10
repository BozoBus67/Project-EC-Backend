"""Authorization gates that mirror the frontend's soft-restriction modals.

These exist because the frontend gates are advisory — a user with curl can
still hit `/create_listing` or `/buy_listing` past the locked-modal layer.
For anything that grants real value (tier upgrades, auction transactions,
real-money flows), enforce server-side too.

Pattern: each gate is a FastAPI dependency factory or dep that builds on
`require_user`. Use them in route signatures the same way:

    @router.post("/create_listing")
    def create_listing(body: ..., user=Depends(require_min_tier(2))):
        ...

The dep returns the same `user` object as `require_user`, so handlers don't
need to change anything else.
"""
from typing import Callable

from fastapi import Depends, HTTPException

from data.account_tiers import ACCOUNT_TIERS
from db.client import supabase
from services.auth import require_user

_TIER_NAME = {i: t["id"].removeprefix("account_tier_") for i, t in enumerate(ACCOUNT_TIERS)}


def require_min_tier(min_tier: int) -> Callable:
  """Dep factory: rejects users below `min_tier` (0-indexed, matching ACCOUNT_TIERS).

  Costs one extra Supabase read per gated request. If you're already going
  to read `premium_game_data` in the handler, that's a duplicate read —
  acceptable for low-traffic endpoints, optimize later if it bites.
  """
  def dep(user=Depends(require_user)):
    pgd = supabase.table("User_Login_Data").select("premium_game_data").eq("id", user.id).single().execute().data["premium_game_data"]
    tier = int(pgd["account_tier"].removeprefix("account_tier_"))
    if tier < min_tier:
      raise HTTPException(status_code=403, detail=f"This action requires account tier {min_tier} or higher.")
    return user
  return dep


def require_real_account(user=Depends(require_user)):
  """Rejects anonymous Supabase users. Use for flows that only make sense
  on a persistent account — currently nothing in production needs this, but
  the dep is here so future real-money or social features can grab it without
  reinventing the check."""
  if getattr(user, "is_anonymous", False):
    raise HTTPException(status_code=403, detail="You must sign up or log in to do this.")
  return user
