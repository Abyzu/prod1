import httpx
import tempfile
from typing import Any
from fastapi import HTTPException, status
from prod1.utils.freshdesk import send_note
from prod1.model import VoucherTicket


async def fetch_voucher(voucherTicket: VoucherTicket) -> Any:
    url = f"https://www.fabmailers.in/company/v1/corporate/admin/bookings/get/booking/voucher/{voucherTicket.voucher.booking_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Referer": "https://www.fabmailers.in/admin/orion/travel/bookings/hotels/ongoing",
        "Cookie": "visitorid=CpYMA2cDuRe2LwPUBDkpAg==; token=e839d6d9-59e9-4fff-86ac-43c1d3ea1655;".encode(
            "utf-8"
        ),
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=0",
        "TE": "trailers",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response = response.json()
            response["file_name"] = await _fetch_document(client, response["data"])
            await send_note(
                {
                    "body": f"Voucher: {response["data"]} ",
                    "private": True,
                    "notify_emails": ["anshul.sharma@fabhotels.com"],
                },
                ticket_id=voucherTicket.ticket_id,
            )
            return response
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code, detail="Failed to fetch voucher data."
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while contacting the voucher service.",
        )


async def _fetch_document(client: httpx.AsyncClient, url: str):
    try:
        response = await client.get(url, timeout=10)
        with tempfile.NamedTemporaryFile() as file:
            file.write(response.content)
            file_name = file.name

        return file_name
    except httpx.TimeoutException:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# you are helpful assistant who answer to user query regarding vouchers only dont answer any other query just tell the user that you cant help, and only calls function when user asks for voucher for his booking id
