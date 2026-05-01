"""Tests for buy_listing — the auction-house's multi-user transaction.

The endpoint is a series of side-effecting calls: spend buyer's payment,
credit seller's payment, credit buyer with the item, delete the listing.
We verify the call sequence rather than fake the full DB, since the
service helpers (spend_tokens, add_tokens, spend_cookies, add_cookies)
have their own dedicated tests via test_account_tiers / test_checkins
patterns and are correct in isolation.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from tests._fake_supabase import Fake_Supabase


@pytest.fixture
def patched(monkeypatch):
  from routers import auction_house

  fake = Fake_Supabase()
  spend_tokens_calls = []
  spend_cookies_calls = []
  add_tokens_calls = []
  add_cookies_calls = []

  monkeypatch.setattr(auction_house, "supabase", fake)
  monkeypatch.setattr(auction_house, "spend_tokens", lambda uid, amt: spend_tokens_calls.append((uid, amt)) or 0)
  monkeypatch.setattr(auction_house, "spend_cookies", lambda uid, amt: spend_cookies_calls.append((uid, amt)) or 0)
  monkeypatch.setattr(auction_house, "add_tokens", lambda uid, amt: add_tokens_calls.append((uid, amt)) or 0)
  monkeypatch.setattr(auction_house, "add_cookies", lambda uid, amt: add_cookies_calls.append((uid, amt)) or 0)

  return SimpleNamespace(
    module=auction_house,
    fake=fake,
    spend_tokens_calls=spend_tokens_calls,
    spend_cookies_calls=spend_cookies_calls,
    add_tokens_calls=add_tokens_calls,
    add_cookies_calls=add_cookies_calls,
  )


def _user(uuid="buyer-1"):
  return SimpleNamespace(id=uuid)


class _MultiRowFake(Fake_Supabase):
  """Fake that returns different rows for sequential `single().execute()` calls.

  buy_listing makes several different selects in sequence; this lets a test
  enqueue what each one should return.
  """
  def __init__(self, single_responses):
    super().__init__()
    self._single_queue = list(single_responses)

  def table(self, _name):
    return _MultiRowFakeTable(self)


class _MultiRowFakeTable:
  def __init__(self, parent):
    self.parent = parent
    self.mode = "select"
    self.update_payload = None
    self.is_single = False

  def select(self, _cols):
    self.mode = "select"
    return self

  def update(self, payload):
    self.mode = "update"
    self.update_payload = payload
    return self

  def insert(self, payload):
    self.mode = "insert"
    return self

  def delete(self):
    self.mode = "delete"
    return self

  def eq(self, _col, _val):
    return self

  def neq(self, _col, _val):
    return self

  def single(self):
    self.is_single = True
    return self

  def execute(self):
    from tests._fake_supabase import _Fake_Result
    if self.mode == "update":
      self.parent.last_update = self.update_payload
      return _Fake_Result(data=None)
    if self.mode == "delete":
      self.parent.last_delete = True
      return _Fake_Result(data=None)
    # select
    if self.parent._single_queue:
      return _Fake_Result(data=self.parent._single_queue.pop(0))
    return _Fake_Result(data=None)


def test_buy_listing_token_priced_charges_buyer_and_pays_seller(monkeypatch):
  from routers import auction_house

  fake = _MultiRowFake([
    # 1. listing select
    {"id": "L1", "seller_username": "alice", "selling_item_type": "cookies",
     "amount": 100, "price_item_type": "tokens", "price_item_amount": 5},
    # 2. seller_id lookup
    {"id": "seller-uuid"},
    # 3. final buyer state read
    {"game_data": {"quantity": 100}, "premium_game_data": {"tokens": 0}},
  ])
  spend_tokens_calls = []
  add_tokens_calls = []
  add_cookies_calls = []
  monkeypatch.setattr(auction_house, "supabase", fake)
  monkeypatch.setattr(auction_house, "spend_tokens", lambda uid, amt: spend_tokens_calls.append((uid, amt)) or 0)
  monkeypatch.setattr(auction_house, "add_tokens", lambda uid, amt: add_tokens_calls.append((uid, amt)) or 0)
  monkeypatch.setattr(auction_house, "add_cookies", lambda uid, amt: add_cookies_calls.append((uid, amt)) or 0)

  result = auction_house.buy_listing(auction_house.ListingRequest(listing_id="L1"), user=_user("buyer-1"))

  assert spend_tokens_calls == [("buyer-1", 5)]
  assert add_tokens_calls == [("seller-uuid", 5)]
  assert add_cookies_calls == [("buyer-1", 100)]
  assert fake.last_delete is True
  assert result["status"] == "ok"


def test_buy_listing_cookie_priced_uses_cookie_helpers(monkeypatch):
  from routers import auction_house

  fake = _MultiRowFake([
    {"id": "L1", "seller_username": "alice", "selling_item_type": "tokens",
     "amount": 3, "price_item_type": "cookies", "price_item_amount": 200},
    {"id": "seller-uuid"},
    {"game_data": {"quantity": 0}, "premium_game_data": {"tokens": 3}},
  ])
  spend_cookies_calls = []
  add_cookies_calls = []
  add_tokens_calls = []
  monkeypatch.setattr(auction_house, "supabase", fake)
  monkeypatch.setattr(auction_house, "spend_cookies", lambda uid, amt: spend_cookies_calls.append((uid, amt)) or 0)
  monkeypatch.setattr(auction_house, "add_cookies", lambda uid, amt: add_cookies_calls.append((uid, amt)) or 0)
  monkeypatch.setattr(auction_house, "add_tokens", lambda uid, amt: add_tokens_calls.append((uid, amt)) or 0)

  result = auction_house.buy_listing(auction_house.ListingRequest(listing_id="L1"), user=_user("buyer-1"))

  assert spend_cookies_calls == [("buyer-1", 200)]
  assert add_cookies_calls == [("seller-uuid", 200)]
  assert add_tokens_calls == [("buyer-1", 3)]
  assert fake.last_delete is True


def test_buy_listing_rejects_buying_own_listing(monkeypatch):
  from routers import auction_house

  fake = _MultiRowFake([
    {"id": "L1", "seller_username": "me", "selling_item_type": "cookies",
     "amount": 1, "price_item_type": "tokens", "price_item_amount": 1},
    {"id": "buyer-1"},  # seller_id same as buyer
  ])
  monkeypatch.setattr(auction_house, "supabase", fake)

  with pytest.raises(HTTPException) as exc:
    auction_house.buy_listing(auction_house.ListingRequest(listing_id="L1"), user=_user("buyer-1"))

  assert exc.value.status_code == 400
  assert "own listing" in exc.value.detail.lower()
  assert fake.last_delete is False


def test_buy_listing_404_when_listing_missing(monkeypatch):
  from routers import auction_house

  fake = _MultiRowFake([None])  # listing select returns None
  monkeypatch.setattr(auction_house, "supabase", fake)

  with pytest.raises(HTTPException) as exc:
    auction_house.buy_listing(auction_house.ListingRequest(listing_id="L999"), user=_user())

  assert exc.value.status_code == 404
  assert "not found" in exc.value.detail.lower()
