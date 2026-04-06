from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import stripe
import os
from supabase import create_client

load_dotenv()

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

app = FastAPI()

@app.get("/")
def root():
  return {"status": "ok"}

@app.post("/premium_payment_1")
async def premium_payment_1(request: Request):
  payload = await request.body()
  sig_header = request.headers.get("stripe-signature")

  try:
    event = stripe.Webhook.construct_event(
      payload, sig_header, STRIPE_WEBHOOK_SECRET
    )
  except Exception:
    raise HTTPException(status_code=400, detail="Invalid signature")

  if event["type"] == "checkout.session.completed":
    session = event["data"]["object"]
    username = session.get("client_reference_id")

    if username:
      supabase.table("User_Login_Data").update(
        {"account_tier": "premium"}
      ).eq("username", username).execute()

  return {"status": "ok"}
