"""
Postmark Email Client
Handles all Postmark API interactions for sending/receiving emails.
"""

import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.config import settings
from utils.logger import logger


POSTMARK_BASE_URL = "https://api.postmarkapp.com"


def _get_headers() -> Dict[str, str]:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Postmark-Server-Token": settings.POSTMARK_SERVER_TOKEN or "",
    }


async def send_email(
    to: str,
    subject: str,
    html_body: str = "",
    text_body: str = "",
    from_email: str = None,
    reply_to: str = None,
    cc: str = None,
    bcc: str = None,
    tag: str = None,
    track_opens: bool = True,
    track_links: str = "HtmlAndText",
    attachments: List[Dict] = None,
    metadata: Dict[str, str] = None,
    message_stream: str = "outbound",
) -> Dict[str, Any]:
    """Send an email via Postmark API."""
    
    payload = {
        "From": from_email or settings.POSTMARK_FROM_EMAIL or "noreply@example.com",
        "To": to,
        "Subject": subject,
        "HtmlBody": html_body,
        "TextBody": text_body or html_body,
        "MessageStream": message_stream,
        "TrackOpens": track_opens,
        "TrackLinks": track_links,
    }
    
    if reply_to:
        payload["ReplyTo"] = reply_to
    if cc:
        payload["Cc"] = cc
    if bcc:
        payload["Bcc"] = bcc
    if tag:
        payload["Tag"] = tag
    if attachments:
        payload["Attachments"] = attachments
    if metadata:
        payload["Metadata"] = metadata
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{POSTMARK_BASE_URL}/email",
                headers=_get_headers(),
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Postmark send_email error: {e}")
        return {"error": str(e), "ErrorCode": -1}


async def get_inbound_message(message_id: str) -> Dict[str, Any]:
    """Get details of a specific inbound message."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{POSTMARK_BASE_URL}/messages/inbound/{message_id}/details",
                headers=_get_headers(),
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Postmark get_inbound_message error: {e}")
        return {"error": str(e)}


async def list_inbound_messages(
    count: int = 50,
    offset: int = 0,
    recipient: str = None,
    from_email: str = None,
    tag: str = None,
    status: str = None,
    from_date: datetime = None,
    to_date: datetime = None,
) -> Dict[str, Any]:
    """List inbound messages with optional filtering."""
    params = {
        "count": count,
        "offset": offset,
    }
    if recipient:
        params["recipient"] = recipient
    if from_email:
        params["fromemail"] = from_email
    if tag:
        params["tag"] = tag
    if status:
        params["status"] = status
    if from_date:
        params["fromdate"] = from_date.isoformat()
    if to_date:
        params["todate"] = to_date.isoformat()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{POSTMARK_BASE_URL}/messages/inbound",
                headers=_get_headers(),
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Postmark list_inbound_messages error: {e}")
        return {"error": str(e), "InboundMessages": [], "TotalCount": 0}


async def create_sender_signature(
    name: str,
    from_email: str,
    reply_to_email: str = None,
    return_path_domain: str = None,
) -> Dict[str, Any]:
    """Create a new sender signature for verified sending."""
    payload = {
        "Name": name,
        "FromEmail": from_email,
    }
    if reply_to_email:
        payload["ReplyToEmail"] = reply_to_email
    if return_path_domain:
        payload["ReturnPathDomain"] = return_path_domain
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{POSTMARK_BASE_URL}/senders",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=30.0
                    "X-Postmark-Account-Token": settings.POSTMARK_ACCOUNT_TOKEN or settings.POSTMARK_SERVER_TOKEN or "",
                },
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Postmark create_sender_signature error: {e}")
        return {"error": str(e)}


async def get_server_info() -> Dict[str, Any]:
    """Get information about the Postmark server."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{POSTMARK_BASE_URL}/server",
                headers=_get_headers(),
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Postmark get_server_info error: {e}")
        return {"error": str(e), "Name": "Unknown", "ServerLink": ""}
