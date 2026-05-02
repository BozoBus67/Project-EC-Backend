"""Drift tests for the scroll registry. Adding a slug to MASTERY_SCROLLS
without also adding it to INITIAL_PREMIUM_GAME_DATA produces a runtime "missing
key" 500 the first time anyone wins that scroll. These tests catch that gap
at CI time, before deploy.

Cross-repo drift (backend slug list vs. frontend scroll_registry.js) is NOT
tested here — that contract is enforced at runtime by `increase_mastery_scroll`
rejecting unknown slugs. The frontend has its own mirror test in
`vite_part_react/src/shared/scroll_registry.test.js`."""

import re

from data.premium_game_data import INITIAL_PREMIUM_GAME_DATA
from data.scrolls import MASTERY_SCROLLS, SCROLL_TIERS
from services.scrolls import get_scroll_tier


def test_every_scroll_slug_initialized_in_premium_game_data():
  missing = [slug for slug in MASTERY_SCROLLS if slug not in INITIAL_PREMIUM_GAME_DATA]
  assert not missing, (
    f"Slugs in MASTERY_SCROLLS but missing from INITIAL_PREMIUM_GAME_DATA: {missing}. "
    "New users would crash on first win for these slugs."
  )


def test_every_scroll_slug_defaults_to_zero():
  bad = {slug: INITIAL_PREMIUM_GAME_DATA[slug] for slug in MASTERY_SCROLLS if INITIAL_PREMIUM_GAME_DATA[slug] != 0}
  assert not bad, f"Scroll slugs in INITIAL_PREMIUM_GAME_DATA must default to 0, got: {bad}"


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")

def test_scroll_slugs_are_well_formed():
  bad = [slug for slug in MASTERY_SCROLLS if not SLUG_PATTERN.match(slug)]
  assert not bad, f"Scroll slugs must be lowercase snake_case: {bad}"


def test_scroll_slugs_are_unique():
  # dict keys are inherently unique, but if the file ever becomes a list of
  # tuples or similar, this guards against duplicates.
  slugs = list(MASTERY_SCROLLS.keys())
  assert len(slugs) == len(set(slugs)), f"Duplicate scroll slugs: {[s for s in slugs if slugs.count(s) > 1]}"


def test_scroll_tiers_descending_so_first_match_wins():
  mins = [t["min"] for t in SCROLL_TIERS]
  assert mins == sorted(mins, reverse=True), (
    f"SCROLL_TIERS must be in descending min order so get_scroll_tier returns "
    f"the highest matching tier on first hit. Got mins: {mins}"
  )


def test_get_scroll_tier_boundaries():
  # Edge case sweep covering every tier boundary defined in scrolls.py.
  assert get_scroll_tier(0) == 0
  assert get_scroll_tier(1) == 1
  assert get_scroll_tier(3) == 1
  assert get_scroll_tier(4) == 2
  assert get_scroll_tier(9) == 2
  assert get_scroll_tier(10) == 3
  assert get_scroll_tier(24) == 3
  assert get_scroll_tier(25) == 4
  assert get_scroll_tier(99) == 4
  assert get_scroll_tier(100) == 5
  assert get_scroll_tier(10_000) == 5
