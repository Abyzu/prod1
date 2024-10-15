import os
from fastapi import HTTPException
import httpx
import asyncio


async def send_note(payload, ticket_id: int = 100128):
    domain = "tpsandbox.freshdesk.com"
    api_key = os.getenv("FRESHDESK_API_KEY", "nUv55yehcQ8RpmfbKe")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")

    url = f"https://{domain}/api/v2/tickets/{ticket_id}/notes"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, auth=(api_key, "X"), json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as err:
        raise HTTPException(
            status_code=err.response.status_code,
            detail=f"Failed to generate note: {err.response.text}",
        )
    except httpx.RequestError as err:
        raise HTTPException(status_code=500, detail=f"Network error occurred: {err}")


if __name__ == "__main__":
    asyncio.run(
        send_note(
            payload={
                "body": "note text",
                "private": True,
                "notify_emails": ["anshul.sharma@fabhotels.com"],
            }
        )
    )
