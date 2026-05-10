from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel

from services.analytics import capture as analytics_capture
from services.auth import require_user

router = APIRouter()

# Heartbeat from the frontend's active-time loop. The frontend POSTs this
# once every minute while the app is focused; counting these events in
# PostHog × the ping interval gives total active time per user.
#
# Body is optional for backward compatibility — old frontends that haven't
# refreshed since this change still POST with no body, and we capture the
# event without URL/screen rather than 422-ing them. Once everyone's
# reloaded, every ping will carry $current_url and the PostHog "URL/SCREEN"
# column populates.
class ActivePingBody(BaseModel):
  url: str | None = None
  screen: str | None = None

@router.post("/active_ping")
def active_ping(
  user=Depends(require_user),
  body: ActivePingBody | None = Body(default=None),
):
  properties: dict = {}
  if body:
    # PostHog reserves keys prefixed with `$` for built-in dashboard semantics
    # ($current_url populates the URL/SCREEN column on web events).
    if body.url: properties["$current_url"] = body.url
    if body.screen: properties["$pathname"] = body.screen
  analytics_capture(distinct_id=user.id, event="active_ping", properties=properties)
  return {"status": "ok"}
