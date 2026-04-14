from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Literal
from utils import require_user
from initializations_and_declarations.db_initialization import supabase

router = APIRouter()

class CreateListingRequest(BaseModel):
  listing_type: Literal["tokens", "cookies"]
  amount: int
  price: int

class ListingRequest(BaseModel):
  listing_id: str

@router.post("/create_listing")
def create_listing(body: CreateListingRequest, user=Depends(require_user)):
  # TODO: implement
  return {"status": "ok"}

@router.get("/get_listings")
def get_listings():
  result = supabase.table("Auction_House").select("*").execute()
  return result.data

@router.post("/buy_listing")
def buy_listing(body: ListingRequest, user=Depends(require_user)):
  # TODO: implement
  return {"status": "ok"}

@router.post("/cancel_listing")
def cancel_listing(body: ListingRequest, user=Depends(require_user)):
  # TODO: implement
  return {"status": "ok"}