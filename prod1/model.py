from datetime import date
from pydantic import BaseModel
from datetime import datetime


class Ticket(BaseModel):
    ticket_id: int
    ticket_subject: str
    ticket_description: str
    ticket_url: str
    model_config = {"extra": "forbid"}


class Voucher(BaseModel):
    booking_id: str


class Options(BaseModel):
    city: str = ""
    locality: str = ""
    checkIn: str = datetime.today().strftime("%Y-%m-%d")
    checkOut: str = ""
    # latitude: float
    # longitude: float
    countryCode: str = "IN"
    countryName: str = "India"
    miscellaneous: str = "OutOfPolicy"
    preferredLocation: bool = False
    occupancy: int = 1


class VoucherTicket(Ticket):
    voucher: Voucher


class OptionsTicket(Ticket):
    options: Options


class Property(BaseModel):
    id: int
    name: str
    city: str
    locality: str
    landmarkDistance: str
    starRating: str
    otaRate: int
    propertyCategory: str
    address: str
