import os
import openai
import json
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from ..services.vouchers import fetch_voucher

logger = logging.getLogger("router")
logger.setLevel(logging.INFO)


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
            "name": "get_voucher",
            "description": "call the api after getting booking_id",
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
    }
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
                "content": "you are helpful assistant who answer to user query regarding vouchers only dont answer any other query just tell the user that you cant help, and only calls function when user asks for voucher for his booking id",
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
            try:
                voucher_response = await fetch_voucher(**args)
                print(voucher_response)
                return {"message": voucher_response}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Voucher service error: {str(e)}",
                )

        return {"message": None}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
