import os
import openai
import json
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from prod1.services.vouchers import fetch_voucher
from prod1.services.optionSharing import get
from prod1.model import OptionsTicket, Options, Voucher, VoucherTicket

logger = logging.getLogger("router")
logger.setLevel(logging.INFO)

openai.api_key = "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"

router = APIRouter()


class Response(BaseModel):
    response: str


class Email_Data(BaseModel):
    ticket_id: int
    ticket_subject: str
    ticket_description: str
    ticket_url: str
    model_config = {"extra": "forbid"}


class Payload(BaseModel):
    freshdesk_webhook: Email_Data


tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch_voucher",
            "description": "call the api when the user is asking to share voucher",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "booking_id, e.g. DXNXWX",
                    },
                },
                "required": ["booking_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_options",
            "description": "call the api when user is asking to book hotel",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "city, e.g. mumbai",
                    },
                    "minPrice": {
                        "type": "integer",
                        "description": "minimum price for hotel",
                    },
                    "maxPrice": {
                        "type": "integer",
                        "description": "maximum price for hotel",
                    },
                    "checkIn": {
                        "type": "string",
                        "description": "date of checkin",
                    },
                    "checkOut": {
                        "type": "string",
                        "description": "date of checkout",
                    },
                },
                "required": [],
            },
        },
    },
]


async def get_completion(
    messages,
    model="gpt-4o",
    temperature=0,
    max_tokens=300,
    tools=None,
    tool_choice="auto",
):
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice="auto",
        )
        return response.choices[0].message
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API error: {e}",
        )


@router.post("/demo", status_code=status.HTTP_200_OK, tags=["base"])
async def classify(data: Payload):
    try:
        messages = [
            {
                "role": "system",
                "content": "you are helpful assistant and your job is to decide which function to call based on the following content",
            },
            {
                "role": "user",
                "content": f"Subject: {data.freshdesk_webhook.ticket_subject}\nBody: {data.freshdesk_webhook.ticket_description}",
            },
        ]
        response = await get_completion(messages=messages, tools=tools)
        if not response:
            raise HTTPException(
                status_code=status.HTTP_302_FOUND,
                detail="No valid response received from OpenAI.",
            )
        if hasattr(response, "tool_calls") and response.tool_calls:
            args = json.loads(response.tool_calls[0].function.arguments)
            match response.tool_calls[0].function.name:
                case "fetch_voucher":
                    try:
                        voucherTicket = VoucherTicket(
                            **data.freshdesk_webhook.model_dump(),
                            voucher=Voucher(**args),
                        )
                        voucher_response = await fetch_voucher(voucherTicket)
                        return {"message": voucher_response}

                    except Exception as e:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Voucher service error: {str(e)}",
                        )
                case "fetch_options":
                    try:
                        options = OptionsTicket(
                            **data.freshdesk_webhook.model_dump(),
                            options=Options(**args),
                        )
                        option_response = await get(options)
                        return {"message": option_response}
                    except Exception as e:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"options service error: {str(e)}",
                        )
        return {"message": None}

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
