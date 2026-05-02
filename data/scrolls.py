# Mastery-scroll registry. Slug-keyed: each scroll's id is a stable lowercase
# string (matches its image-asset filename basename in the frontend), set once
# and never reused. Adding a scroll = adding one entry here + the frontend
# scroll_registry.js + the image asset. No positional shifting, no migrations.
#
# Order in this dict is irrelevant to gameplay — it's just iteration order for
# the slot machine and the /get_scroll_metadata response. Kept alphabetical
# to match the frontend registry for diff-readability.

MASTERY_SCROLLS = {
  "6_7_kid":             {},
  "adolf_hitler":        {},
  "blurry_epstein":      {},
  "caseoh":              {},
  "charlie_kirk":        {},
  "dexter":              {},
  "diddy":               {},
  "doakes":              {},
  "donald_trump":        {},
  "drake":               {},
  "elon_musk":           {},
  "freddy_fazbear":      {},
  "george_floyd":        {},
  "hillary_clinton":     {},
  "ishowspeed":          {},
  "kai_cenat":           {},
  "khaby_lame":          {},
  "mark_zuckerberg":     {},
  "mr_beast":            {},
  "ninja_from_fortnite": {},
  "roy_lee":             {},
  "state_trooper_cop":   {},
  "stephen_hawking":     {},
  "tun_tun_tun_sahur":   {},
  "walter_white":        {},
}

# Tier thresholds for owned-count → tier badge. Descending order so callers
# can return on first match (highest tier wins).
SCROLL_TIERS = [
  {"min": 100, "tier": 5},
  {"min": 25,  "tier": 4},
  {"min": 10,  "tier": 3},
  {"min": 4,   "tier": 2},
  {"min": 1,   "tier": 1},
]
