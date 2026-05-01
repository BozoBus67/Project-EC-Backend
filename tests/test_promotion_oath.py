"""Tests for the /promotion_oath one-time redeem endpoint.

The endpoint is a thin honour-system grant: no body, no validation beyond
checking whether the user has already claimed it. Pin the three cases —
first claim, repeat claim, that the redeemed flag is written back.
"""
import copy
from types import SimpleNamespace

import pytest

from data.premium_game_data import INITIAL_PREMIUM_GAME_DATA
from tests._fake_supabase import Fake_Supabase


@pytest.fixture
def patched_module(monkeypatch):
  from routers.redeem import promotion_oath
  fake = Fake_Supabase()
  monkeypatch.setattr(promotion_oath, "supabase", fake)
  return promotion_oath, fake


def _user(uuid="user-1"):
  return SimpleNamespace(id=uuid)


def _row_with(redeemed=None, tokens=0):
  pgd = copy.deepcopy(INITIAL_PREMIUM_GAME_DATA)
  pgd["tokens"] = tokens
  if redeemed is not None:
    pgd["redeemed"] = redeemed
  return {"premium_game_data": pgd}


def test_first_claim_grants_reward_and_marks_redeemed(patched_module):
  promotion_oath, fake = patched_module
  fake.row = _row_with(tokens=100)

  result = promotion_oath.promotion_oath(user=_user())

  assert result["already_redeemed"] is False
  assert result["tokens_awarded"] == promotion_oath.REWARD
  # tokens credited
  assert fake.last_update["premium_game_data"]["tokens"] == 100 + promotion_oath.REWARD
  # redeemed flag persisted
  assert fake.last_update["premium_game_data"]["redeemed"]["promotion_oath"] is True


def test_second_claim_returns_already_redeemed_no_grant(patched_module):
  promotion_oath, fake = patched_module
  fake.row = _row_with(redeemed={"promotion_oath": True}, tokens=100)

  result = promotion_oath.promotion_oath(user=_user())

  assert result["already_redeemed"] is True
  assert "tokens_awarded" not in result
  # no DB write — already-redeemed path is a pure read
  assert fake.last_update is None


def test_first_claim_preserves_other_redeemed_flags(patched_module):
  # If the user has already redeemed the Poisson offer, claiming the
  # promotion shouldn't wipe that flag.
  promotion_oath, fake = patched_module
  fake.row = _row_with(redeemed={"poisson": True}, tokens=0)

  promotion_oath.promotion_oath(user=_user())

  redeemed_after = fake.last_update["premium_game_data"]["redeemed"]
  assert redeemed_after["poisson"] is True
  assert redeemed_after["promotion_oath"] is True
