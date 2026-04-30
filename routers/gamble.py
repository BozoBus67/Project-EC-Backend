import random
from fastapi import APIRouter, Depends
from services.auth import require_user
from services.tokens import spend_tokens
from services.scrolls import increase_mastery_scroll
from services.slots import generate_slot_sequence, compute_wins
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
  wins = compute_wins(results, subset_indices, SCROLL_KEYS, REWARDS)
  for win in wins:
    increase_mastery_scroll(user.id, win["scroll_id"], win["amount"])

  return {"sequences": sequences, "subset_indices": subset_indices, "tokens_remaining": tokens_remaining, "wins": wins}

@router.post("/roulette_spin")
def roulette_spin(user=Depends(require_user)):
  tokens_remaining = spend_tokens(user.id, ROULETTE_SPIN_COST)
  scroll_id = random.choice(SCROLL_KEYS)
  increase_mastery_scroll(user.id, scroll_id, ROULETTE_REWARD_AMOUNT)
  return {"tokens_remaining": tokens_remaining, "scroll_id": scroll_id}
