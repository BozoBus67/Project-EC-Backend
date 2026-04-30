import random
from collections import Counter

def generate_slot_sequence(count: int, length: int, rows: int = 3) -> list[list[int]]:
  return [[random.randint(0, count - 1) for _ in range(length)] for _ in range(rows)]

def compute_wins(results: list[int], subset_indices: list[int], scroll_keys: list[str], rewards: dict[int, int]) -> list[dict]:
  """Given the final reel values from one slot spin, return one win entry per
  matching group of size >= 2. Multiple groups (e.g. two pairs) all win
  independently — the rewards table maps group size to scroll amount.
  """
  wins = []
  for value, count in Counter(results).items():
    if count >= 2:
      wins.append({
        "scroll_id": scroll_keys[subset_indices[value]],
        "amount": rewards[count],
      })
  return wins
