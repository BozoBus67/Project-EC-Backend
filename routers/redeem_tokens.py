from fastapi import APIRouter, Depends
from pydantic import BaseModel
from utils import require_user, add_tokens

router = APIRouter()

CORRECT_ANSWERS = {"text1", "text2", "text3"}
REWARD = 100

class RedeemRequest(BaseModel):
  answer_1: str
  answer_2: str
  answer_3: str

@router.post("/redeem_tokens")
def redeem_tokens(body: RedeemRequest, user=Depends(require_user)):
  submitted = {body.answer_1.strip().lower(), body.answer_2.strip().lower(), body.answer_3.strip().lower()}
  if submitted != CORRECT_ANSWERS:
    return {"correct": False}
  add_tokens(user.id, REWARD)
  return {"correct": True, "tokens_awarded": REWARD}
