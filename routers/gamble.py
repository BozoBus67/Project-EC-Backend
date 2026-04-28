from fastapi import APIRouter, Depends
from utils import require_user, generate_slot_sequence

router = APIRouter()

@router.post("/spin")
def spin(user=Depends(require_user)):
    return {"sequences": generate_slot_sequence()}
