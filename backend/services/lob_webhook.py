from fastapi import APIRouter, HTTPException, Request
import os
import lob

router = APIRouter(prefix="/api/lob", tags=["Lob Webhook"])

lob_client = lob.Lob(api_key=os.environ.get("LOB_API_KEY"))


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
