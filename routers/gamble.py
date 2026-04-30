import random
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from services.auth import require_user
from services.tokens import spend_tokens
from services.scrolls import increase_mastery_scroll, UserDataMissingKey
from services.slots import generate_slot_sequence
from services.migrations import ensure_user_data_complete
from data.scrolls import MASTERY_SCROLLS
from constants.constants import SLOT_REEL_LENGTH, SLOT_ALPHABET_SIZE

router = APIRouter()

SPIN_COST = 1
REEL_COUNT = 5
SCROLL_KEYS = list(MASTERY_SCROLLS.keys())
REWARDS = {2: 1, 3: 3, 4: 10, 5: 100}

ROULETTE_SPIN_COST = 1
ROULETTE_REWARD_AMOUNT = 1

@router.post("/spin")
def spin(user=Depends(require_user)):
  tokens_remaining = spend_tokens(user.id, SPIN_COST)

  subset_indices = random.sample(range(len(SCROLL_KEYS)), SLOT_ALPHABET_SIZE)
  sequences = generate_slot_sequence(count=SLOT_ALPHABET_SIZE, length=SLOT_REEL_LENGTH, rows=REEL_COUNT)

  results = [seq[-1] for seq in sequences]
  most_common_val, most_common_count = Counter(results).most_common(1)[0]

  win = None
  if most_common_count >= 2:
    scroll_id = SCROLL_KEYS[subset_indices[most_common_val]]
    amount = REWARDS[most_common_count]
    increase_mastery_scroll(user.id, scroll_id, amount)
    win = {"scroll_id": scroll_id, "amount": amount}

  return {"sequences": sequences, "subset_indices": subset_indices, "tokens_remaining": tokens_remaining, "win": win}

@router.post("/roulette_spin")
def roulette_spin(user=Depends(require_user)):
  tokens_remaining = spend_tokens(user.id, ROULETTE_SPIN_COST)
  scroll_id = random.choice(SCROLL_KEYS)
  migration_info = None
  try:
    increase_mastery_scroll(user.id, scroll_id, ROULETTE_REWARD_AMOUNT)
  except UserDataMissingKey as e:
    migration_info = ensure_user_data_complete(user.id)
    try:
      increase_mastery_scroll(user.id, scroll_id, ROULETTE_REWARD_AMOUNT)
    except UserDataMissingKey as e2:
      raise HTTPException(status_code=500, detail=f"Migration ran but user {e2.user_uuid} still missing key '{e2.key}'. Migration info: {migration_info}")
  return {"tokens_remaining": tokens_remaining, "scroll_id": scroll_id, "migration_info": migration_info}
