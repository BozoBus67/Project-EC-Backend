from fastapi import APIRouter, Depends
from utils import require_user, generate_slot_sequence, spend_tokens, increase_mastery_scroll
from initializations_and_declarations.scroll_declarations import MASTERY_SCROLLS
from constants.constants import SLOT_REEL_LENGTH

router = APIRouter()

SPIN_COST = 1
SCROLL_KEYS = list(MASTERY_SCROLLS.keys())

@router.post("/spin")
def spin(user=Depends(require_user)):
    tokens_remaining = spend_tokens(user.id, SPIN_COST)
    sequences = generate_slot_sequence(count=len(MASTERY_SCROLLS), length=SLOT_REEL_LENGTH)

    r = [seq[-1] for seq in sequences]

    win = None
    if r[0] == r[1] == r[2]:
        scroll_id = SCROLL_KEYS[r[0]]
        increase_mastery_scroll(user.id, scroll_id, 3)
        win = {"scroll_id": scroll_id, "amount": 3}
    elif r[0] == r[1] or r[1] == r[2] or r[0] == r[2]:
        idx = r[0] if r[0] == r[1] or r[0] == r[2] else r[1]
        scroll_id = SCROLL_KEYS[idx]
        increase_mastery_scroll(user.id, scroll_id, 1)
        win = {"scroll_id": scroll_id, "amount": 1}

    return {"sequences": sequences, "tokens_remaining": tokens_remaining, "win": win}
