import httpx
import tempfile
from typing import Any
from fastapi import HTTPException, status


async def fetch_voucher(booking_id: str) -> Any:
    url = f"https://www.fabmailers.in/company/v1/corporate/admin/bookings/get/booking/voucher/{booking_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Referer": "https://www.fabmailers.in/admin/orion/travel/bookings/hotels/ongoing",
        "Cookie": "visitorid=CpYMA2cDuRe2LwPUBDkpAg==; _vwo_uuid_v2=D0C4C0FA24D9B30E61518278A95711C0A|34ae8581a49a4a9fbec49781baaeccd6; _clck=1voc88k%7C2%7Cfpx%7C0%7C1741; __hstc=156355492.663cae50f99434e2b2c66cd5084870d8.1728297241471.1728629828466.1728645045465.12; hubspotutk=663cae50f99434e2b2c66cd5084870d8; AMP_24295c54f9=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjI3ZWE0Y2RjNi01YzM3LTQ5OTEtYWRhZi03NTlkZTY3M2IwZTYlMjIlMkMlMjJ1c2VySWQlMjIlM0ElMjJ2aWthcy55YWRhdiU0MGZhYmhvdGVscy5jb20lMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzI4NjQ1MDQ0Mjc4JTJDJTI…GLZHERADQW3H3G3%3A20241007%3A1%7CLQHC3VQQ2ZG6ZHFYVF4C2X%3A20241007%3A1%7CETD23PO4JRCR7EYPQSBB43%3A20241007%3A1; WZRK_G=67cd525f3a4e4a789297b200e4f1ccf4; _fbp=fb.1.1728375746898.789974182938170943; _clsk=phdw1s%7C1728645047829%7C4%7C1%7Cw.clarity.ms%2Fcollect; __hssrc=1; PHPSESSID=14nns31kkqnl656u76pavqelp3; PHPSESSID=rvkgm03auf89hmsmjmkifksfig; token=a3d01908-317d-4ee1-8f78-5a934d5e5a86; token=a3d01908-317d-4ee1-8f78-5a934d5e5a86; token=a3d01908-317d-4ee1-8f78-5a934d5e5a86; __hssc=156355492.1.1728645045465".encode(
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
