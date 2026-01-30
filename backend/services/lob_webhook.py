from fastapi import APIRouter, HTTPException, Request
import os
import lob

router = APIRouter(prefix="/api/lob", tags=["Lob Webhook"])


def _get_lob_client():
    from core.config import settings
    api_key = os.environ.get("LOB_API_KEY") or settings.LOB_API_KEY
    if not api_key:
        raise HTTPException(status_code=412, detail="LOB API key not configured")
    if hasattr(lob, "Lob"):
        return lob.Lob(api_key=api_key)
    if hasattr(lob, "Client"):
        return lob.Client(api_key=api_key)
    lob.api_key = api_key
    return lob


@router.post("/send")
async def send_letter(request: Request):
    try:
        data = await request.json()
        to_address = data["to"]
        from_address = data.get(
            "from",
            {
                "name": "FusonEMS Admin",
                "address_line1": "123 Main Street",
                "address_city": "City",
                "address_state": "ST",
                "address_zip": "12345",
                "address_country": "US",
            },
        )
        content_html = data.get("content", "<html><body><h1>FusonEMS</h1></body></html>")

        lob_client = _get_lob_client()
        letter = lob_client.letters.create(
            description="FusonEMS Dispatch Letter",
            to_address=to_address,
            from_address=from_address,
            file=content_html,
            color=True,
        )
        return {"status": "success", "letter_id": letter.id}
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Missing field {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
