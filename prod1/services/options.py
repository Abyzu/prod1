from fastapi import HTTPException, status
import httpx
from pydantic import ValidationError
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
import polling
from typing import Dict, List
import asyncio
import logging

from prod1.model import Options, Property

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize(options: Options) -> str:
    init_url = f"https://www.fabmailers.in/company/v2/corporate/admin/hotel/search/initiate?city={options.city}&locality=Mumbai&checkIn={options.checkIn}&checkOut={options.checkOut}&latitude=19.0759837&longitude=72.8776559&countryCode=IN&countryName=India&miscellaneous=outOfPolicy&preferredLocation=false&occupancy={options.occupancy}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Referer": "https://www.fabmailers.in/admin/orion/travel/bookings/hotels/ongoing",
        "Cookie": "visitorid=CpYMA2cDuRe2LwPUBDkpAg==;token=e839d6d9-59e9-4fff-86ac-43c1d3ea1655".encode(
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
            response = await client.get(init_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "data" not in data or "searchId" not in data["data"]:
                raise ValueError("Invalid response structure, 'searchId' not found.")
            return data["data"]["searchId"]

    except httpx.RequestError as e:
        logger.error(f"An error occurred while requesting {e.request.url!r}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Network error, please try again.",
        )
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Error response {e.response.status_code} while requesting {e.request.url!r}: {e.response.text}"
        )
        raise HTTPException(
            status_code=e.response.status_code, detail="Failed to initialize search."
        )
    except ValueError as e:
        logger.error(f"Invalid response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid response from server.",
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


def poll(options_url: str, headers: dict) -> Dict:
    try:
        with httpx.Client() as client:
            response = client.get(options_url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Polling request error: {str(e)}")
        return {}
    except httpx.HTTPStatusError as e:
        logger.error(f"Polling response error: {str(e)}")
        return {}


async def get_options(options: Options) -> List[Property]:
    print(options)
    try:
        search_id = await initialize(options)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize search: {str(e)}",
        )

    options_url = f"https://www.fabmailers.in/company/v2/corporate/admin/hotel/search?minPrice=0&maxPrice=100000&countryCode=IN&countryName=India&outOfPolicy=true&payAtHotelOnly=false&womenPreferred=false&occupancy=1&city=Mumbai&latitude=19.0759837&longitude=72.8776559&checkIn=2024-10-15&checkOut=2024-10-16&searchId={search_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Referer": "https://www.fabmailers.in/admin/orion/travel/bookings/hotels/ongoing",
        "Cookie": "visitorid=CpYMA2cDuRe2LwPUBDkpAg==;token=e839d6d9-59e9-4fff-86ac-43c1d3ea1655".encode(
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
            polling.poll(
                lambda: poll(options_url, headers)
                .get("data", {})
                .get("allPropertiesFetched", False)
                == True,
                step=1,
                timeout=20,
            )
            response = await client.get(options_url, headers=headers, timeout=10)
            response.raise_for_status()
            response = response.json()
            properties = response.get("data", {}).get("properties", [])
            try:
                top_properties = [Property.model_validate(i) for i in properties[:3]]
                print(top_properties)
            except ValidationError as ve:
                logger.error(f"Validation error when parsing properties: {str(ve)}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Data validation error: {str(ve)}",
                )
            return top_properties

    except polling.TimeoutException:
        logger.error("Polling timed out. Failed to fetch all properties.")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Polling timed out. Failed to fetch all properties.",
        )
    except httpx.RequestError as e:
        logger.error(f"Network error while fetching options: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Network error, please try again.",
        )
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to fetch options: {e.response.status_code}, {e.response.text}"
        )
        raise HTTPException(
            status_code=e.response.status_code, detail="Failed to retrieve options."
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


if __name__ == "__main__":
    asyncio.run(
        get_options(
            Options(
                city="mumbai", checkIn="2024-10-15", checkOut="2024-10-16", occupancy=1
            )
        )
    )
