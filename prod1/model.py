from pydantic import BaseModel



class Ticket(BaseModel):
    ticket_id : int 
    ticket_subject: str
    ticket_description: str
    ticket_url: str
    model_config = {"extra": "forbid"}


class VoucherTicket(Ticket):
    booking_id : str

class OptionsTicket(Ticket):
    pass

