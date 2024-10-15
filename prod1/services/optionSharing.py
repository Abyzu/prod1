from prod1.services.options import get_options
import json
import httpx
from fastapi import HTTPException
from prod1.model import OptionsTicket
from prod1.services.infocheck import infoCheck
from prod1.utils.freshdesk import send_note


async def get(optionsTicket: OptionsTicket):
    """add a private note that contains the three options"""
    # need to call infocheck first
    # if infocheck returns that all fields present
    # call get_options
    if not await infoCheck(optionsTicket.ticket_description, optionsTicket.ticket_id):
        properties = await get_options(optionsTicket.options)
        ticket_id = optionsTicket.ticket_id
        domain = "tpsandbox.freshdesk.com"
        api_key = "nUv55yehcQ8RpmfbKe"

        api = f"https://{domain}/api/v2/tickets/{ticket_id}/notes"

        headers = {"Content-Type": "application/json"}
        data = ""
        for i in properties:
            data += str(i.model_dump())
        print(data)
        payload = {
            "body": f"options: {data}",
            "private": True,
            "notify_emails": ["anshul.sharma@fabhotels.com"],
        }

        # add options.py
        # it gets options and return a list add that list to

        try:
            await send_note(payload, ticket_id=ticket_id)
            return "options successfully shared"
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail="Failed to add note."
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=500,
                detail="An error occurred while contacting the notes service.",
            )

        return "options shared"
    else:
        return "bhang bhosda"
