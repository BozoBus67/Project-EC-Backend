"""Tests for the daily / hourly / 5-minute check-in endpoints in routers/tokens.py.

Streak math is the load-bearing logic worth pinning:
  - first claim ever                  → streak resets to 1
  - claim within the cooldown window  → already_checked_in=True, no token grant
  - claim within the grace window     → streak += 1, tokens granted
  - claim after the grace window      → streak resets to 1, tokens granted
"""
import copy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from data.premium_game_data import INITIAL_PREMIUM_GAME_DATA
from tests._fake_supabase import Fake_Supabase


@pytest.fixture
def patched_tokens(monkeypatch):
  from routers import tokens
  fake = Fake_Supabase()
  monkeypatch.setattr(tokens, "supabase", fake)
  return tokens, fake


def _user(uuid="user-1"):
  return SimpleNamespace(id=uuid)


def _row_with(**pgd_overrides):
  pgd = copy.deepcopy(INITIAL_PREMIUM_GAME_DATA)
  pgd.update(pgd_overrides)
  return {"premium_game_data": pgd}


# ------- daily_checkin -------

def test_daily_first_claim_starts_streak_at_1(patched_tokens):
  tokens, fake = patched_tokens
  fake.row = _row_with(login_streak=0, last_login_date=None, tokens=0)

  result = tokens.daily_checkin(user=_user())

  assert result["already_checked_in"] is False
  assert result["streak"] == 1
  assert result["tokens_granted"] == 25
  assert fake.last_update["premium_game_data"]["tokens"] == 25
  assert fake.last_update["premium_game_data"]["login_streak"] == 1


def test_daily_same_day_is_already_checked_in(patched_tokens):
  tokens, fake = patched_tokens
  today = datetime.now(timezone.utc).date().isoformat()
  fake.row = _row_with(login_streak=3, last_login_date=today, tokens=100)

  result = tokens.daily_checkin(user=_user())

  assert result["already_checked_in"] is True
  assert result["streak"] == 3
  assert fake.last_update is None


def test_daily_consecutive_day_increments_streak(patched_tokens):
  tokens, fake = patched_tokens
  yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
  fake.row = _row_with(login_streak=4, last_login_date=yesterday, tokens=0)

  result = tokens.daily_checkin(user=_user())

  assert result["streak"] == 5
  assert result["tokens_granted"] == 5 * 25  # streak * 25
  assert fake.last_update["premium_game_data"]["login_streak"] == 5


def test_daily_skipped_day_resets_streak(patched_tokens):
  tokens, fake = patched_tokens
  three_days_ago = (datetime.now(timezone.utc).date() - timedelta(days=3)).isoformat()
  fake.row = _row_with(login_streak=10, last_login_date=three_days_ago, tokens=0)

  result = tokens.daily_checkin(user=_user())

  assert result["streak"] == 1
  assert result["tokens_granted"] == 25
  assert fake.last_update["premium_game_data"]["login_streak"] == 1


# ------- hourly_checkin -------

def test_hourly_first_claim_starts_streak_at_1(patched_tokens):
  tokens, fake = patched_tokens
  fake.row = _row_with(hourly_streak=0, last_hourly_claim=None, tokens=0)

  result = tokens.hourly_checkin(user=_user())

  assert result["already_checked_in"] is False
  assert result["streak"] == 1
  assert result["tokens_granted"] == 5


def test_hourly_within_cooldown_is_already_checked_in(patched_tokens):
  tokens, fake = patched_tokens
  recent = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
  fake.row = _row_with(hourly_streak=2, last_hourly_claim=recent, tokens=0)

  result = tokens.hourly_checkin(user=_user())

  assert result["already_checked_in"] is True
  assert fake.last_update is None


def test_hourly_within_grace_increments_streak(patched_tokens):
  tokens, fake = patched_tokens
  # 90 minutes ago → past 1h cooldown but within 2h grace window
  past = (datetime.now(timezone.utc) - timedelta(minutes=90)).isoformat()
  fake.row = _row_with(hourly_streak=3, last_hourly_claim=past, tokens=0)

  result = tokens.hourly_checkin(user=_user())

  assert result["streak"] == 4
  assert result["tokens_granted"] == 4 * 5


def test_hourly_outside_grace_resets_streak(patched_tokens):
  tokens, fake = patched_tokens
  # 3h ago → outside the 2h grace window, streak should reset
  past = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
  fake.row = _row_with(hourly_streak=10, last_hourly_claim=past, tokens=0)

  result = tokens.hourly_checkin(user=_user())

  assert result["streak"] == 1
  assert result["tokens_granted"] == 5


# ------- fivemin_checkin -------

def test_fivemin_first_claim_starts_streak_at_1(patched_tokens):
  tokens, fake = patched_tokens
  fake.row = _row_with(fivemin_streak=0, last_5min_claim=None, tokens=0)

  result = tokens.fivemin_checkin(user=_user())

  assert result["streak"] == 1
  assert result["tokens_granted"] == 1


def test_fivemin_within_cooldown_is_already_checked_in(patched_tokens):
  tokens, fake = patched_tokens
  recent = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
  fake.row = _row_with(fivemin_streak=4, last_5min_claim=recent, tokens=0)

  result = tokens.fivemin_checkin(user=_user())

  assert result["already_checked_in"] is True
  assert fake.last_update is None


def test_fivemin_within_grace_increments_streak(patched_tokens):
  tokens, fake = patched_tokens
  past = (datetime.now(timezone.utc) - timedelta(minutes=7)).isoformat()
  fake.row = _row_with(fivemin_streak=8, last_5min_claim=past, tokens=0)

  result = tokens.fivemin_checkin(user=_user())

  assert result["streak"] == 9
  assert result["tokens_granted"] == 9 * 1


def test_fivemin_outside_grace_resets_streak(patched_tokens):
  tokens, fake = patched_tokens
  past = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
  fake.row = _row_with(fivemin_streak=20, last_5min_claim=past, tokens=0)

  result = tokens.fivemin_checkin(user=_user())

  assert result["streak"] == 1
  assert result["tokens_granted"] == 1
