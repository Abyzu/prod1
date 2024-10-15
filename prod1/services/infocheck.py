# it will recieve the email content after classification
# check if all the details are mentioned(city,minPrice,maxPrice,checkIn,checkOut)
# store for each ticket id in database all the properties recieve till now
# if info is missing call api to add note in FD ticket
# if all info present return true/call options with the details
import json
from openai import OpenAI
from prod1.utils.freshdesk import send_note
from prod1.model import OptionsTicket


# def infoCheck(content,ticket : OptionsTicket):
async def infoCheck(content, ticket):
    """this function check whether all the data required is present in the content"""
    # ask llm
    client = OpenAI(
        api_key=""
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": """check if the following content caontains the info city,minimum price, maximum price and check out.the price/budget in the content is maxPrice until stated otherwise and minimim price if not mentioned should be 0.
            return only json and if a value is missing write NONE as value""",
            },
            {"role": "user", "content": f"""{content}"""},
        ],
    )

    response = response.choices[0].message.content
    # check all values if any is false
    data = json.loads(response)
    false_keys = [key for key, value in data.items() if value == "NONE"]
    # ticket_id = ticket.ticket_id
    ticket_id = ticket
    domain = "tpsandbox.freshdesk.com"
    api_key = "nUv55yehcQ8RpmfbKe"

    api = f"https://{domain}/api/v2/tickets/{ticket_id}/notes"

    headers = {"Content-Type": "application/json"}

    payload = {
        "body": (
            f"Missing info: {', '.join(false_keys)}"
            if false_keys
            else "All information is present."
        ),
        "private": True,
        "notify_emails": ["anshul.sharma@fabhotels.com"],
    }
    if len(false_keys) == 0:
        return False
    try:
        await send_note(payload, ticket_id=ticket_id)
    except Exception as err:
        print(err)
