from services.slots import compute_wins

REWARDS = {2: 1, 3: 3, 4: 10, 5: 100}
SCROLL_KEYS = [f"mastery_scroll_{i}" for i in range(1, 25)]
SUBSET = [10, 11, 12, 13, 14, 15]  # any subset_indices; the test asserts on the resolved scroll ids

def _scrolls(*win_scroll_ids):
  return {sid for sid in win_scroll_ids}


def test_no_matches_no_wins():
  results = [0, 1, 2, 3, 4]
  assert compute_wins(results, SUBSET, SCROLL_KEYS, REWARDS) == []


def test_single_pair_one_win():
  results = [0, 0, 1, 2, 3]
  wins = compute_wins(results, SUBSET, SCROLL_KEYS, REWARDS)
  assert len(wins) == 1
  assert wins[0]["scroll_id"] == SCROLL_KEYS[SUBSET[0]]
  assert wins[0]["amount"] == REWARDS[2]


def test_two_pairs_both_win():
  """Regression: 2x scroll0 + 2x scroll1 used to award only the first pair."""
  results = [0, 0, 1, 1, 2]
  wins = compute_wins(results, SUBSET, SCROLL_KEYS, REWARDS)
  assert len(wins) == 2
  assert _scrolls(*[w["scroll_id"] for w in wins]) == _scrolls(
    SCROLL_KEYS[SUBSET[0]], SCROLL_KEYS[SUBSET[1]]
  )
  assert all(w["amount"] == REWARDS[2] for w in wins)


def test_triple_one_win_higher_amount():
  results = [0, 0, 0, 1, 2]
  wins = compute_wins(results, SUBSET, SCROLL_KEYS, REWARDS)
  assert wins == [{"scroll_id": SCROLL_KEYS[SUBSET[0]], "amount": REWARDS[3]}]


def test_full_house_pair_and_triple_both_win():
  """Triple + pair (full house) — both groups should award."""
  results = [0, 0, 0, 1, 1]
  wins = compute_wins(results, SUBSET, SCROLL_KEYS, REWARDS)
  assert len(wins) == 2
  by_scroll = {w["scroll_id"]: w["amount"] for w in wins}
  assert by_scroll[SCROLL_KEYS[SUBSET[0]]] == REWARDS[3]
  assert by_scroll[SCROLL_KEYS[SUBSET[1]]] == REWARDS[2]


def test_jackpot_five_of_a_kind():
  results = [0, 0, 0, 0, 0]
  wins = compute_wins(results, SUBSET, SCROLL_KEYS, REWARDS)
  assert wins == [{"scroll_id": SCROLL_KEYS[SUBSET[0]], "amount": REWARDS[5]}]


def test_four_of_a_kind_plus_singleton():
  results = [0, 0, 0, 0, 1]
  wins = compute_wins(results, SUBSET, SCROLL_KEYS, REWARDS)
  assert wins == [{"scroll_id": SCROLL_KEYS[SUBSET[0]], "amount": REWARDS[4]}]
