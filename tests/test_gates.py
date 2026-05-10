"""Tests for services/gates.py — the server-side enforcement of the soft
restrictions that have frontend lock-modal counterparts.

Each gate is a FastAPI dependency. We call it directly (bypassing the
require_user chain by passing user= explicitly) and assert that it either
returns the user or raises HTTPException with the right status code.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from tests._fake_supabase import Fake_Supabase


def _user(uuid="user-1", is_anonymous=False):
  return SimpleNamespace(id=uuid, is_anonymous=is_anonymous)


# ------- require_min_tier -------

@pytest.fixture
def patched_gates(monkeypatch):
  from services import gates
  fake = Fake_Supabase()
  monkeypatch.setattr(gates, "supabase", fake)
  return gates, fake


def test_min_tier_passes_when_user_meets_threshold(patched_gates):
  gates, fake = patched_gates
  fake.row = {"premium_game_data": {"account_tier": "account_tier_2"}}

  dep = gates.require_min_tier(2)
  result = dep(user=_user())

  assert result.id == "user-1"


def test_min_tier_passes_when_user_exceeds_threshold(patched_gates):
  gates, fake = patched_gates
  fake.row = {"premium_game_data": {"account_tier": "account_tier_5"}}

  dep = gates.require_min_tier(2)
  result = dep(user=_user())

  assert result.id == "user-1"


def test_min_tier_blocks_user_below_threshold(patched_gates):
  gates, fake = patched_gates
  fake.row = {"premium_game_data": {"account_tier": "account_tier_0"}}

  dep = gates.require_min_tier(2)
  with pytest.raises(HTTPException) as exc:
    dep(user=_user())

  assert exc.value.status_code == 403
  assert "tier" in exc.value.detail.lower()


# ------- require_real_account -------

def test_real_account_passes_for_real_user():
  from services import gates
  result = gates.require_real_account(user=_user(is_anonymous=False))
  assert result.id == "user-1"


def test_real_account_blocks_anonymous_user():
  from services import gates
  with pytest.raises(HTTPException) as exc:
    gates.require_real_account(user=_user(is_anonymous=True))
  assert exc.value.status_code == 403
