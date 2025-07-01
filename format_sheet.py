import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
import json
from enum import Enum

# Path to your downloaded service account key
SERVICE_ACCOUNT_FILE = 'amyhuang-49fcaf834c17.json'

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate and create the client
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Load environment variables from .env file
load_dotenv()
SHEET_URL = os.getenv('GOOGLE_SHEET_URL')

worksheet = client.open_by_url(SHEET_URL).sheet1

# Enums for repeated categorical values
class YesNo(Enum):
    YES = "Yes"
    NO = "No"

class CrashOut(Enum):
    NO_GOOD = "No, everything is good"
    # Add more as needed

class Argument(Enum):
    NO_GOOD = "No, everything is good."
    # Add more as needed

class Period(Enum):
    YES = "Yes"
    NO = "No"

class Coitus(Enum):
    YES = "Yes"
    NO = "No"

class Fellatio(Enum):
    YES = "Yes"
    NO = "No"

class LongDistance(Enum):
    YES = "Yes"
    NO = "No"

# Helper to parse multi-select fields into lists
MULTI_SELECT_FIELDS = [
    'Select all that you feel is true ',
    'Check all that are true for this hangout.'
]

def parse_row(row):
    parsed = {}
    for key, value in row.items():
        value = value.strip() if isinstance(value, str) else value
        # Numeric fields
        if key == 'How strong do you think our relationship is?':
            try:
                parsed[key] = int(value)
            except (ValueError, TypeError):
                parsed[key] = value
        elif key == 'How stressed are you about things outside of our relationship? ':
            try:
                parsed[key] = int(value)
            except (ValueError, TypeError):
                parsed[key] = value
        # Yes/No fields
        elif key in [
            'Do you still like me? ',
            'Was Amy on her period?',
            'Did we have coitus during this hangout?',
            'Did we do fellatio during this hangout?',
            'Did you hang out (in real life)? ',
            'Are you long distance right now?'
        ]:
            parsed[key] = YesNo(value).name if value in YesNo._value2member_map_ else value
        # Categorical fields
        elif key == 'Did you have any crash outs about us? \n\nSomething counts as a crash out if you spent >30 minutes worrying about the relationship, or had a bad thought that lasted multiple days. ':
            parsed[key] = CrashOut(value).name if value in CrashOut._value2member_map_ else value
        elif key == 'Did we argue? \n\nSomething counts as an argument if one party felt anger about something, and brought it up, and it was not immediately resolved. ':
            parsed[key] = Argument(value).name if value in Argument._value2member_map_ else value
        # Multi-select fields
        elif key in MULTI_SELECT_FIELDS:
            parsed[key] = [v.strip() for v in value.split(',')] if value else []
        else:
            parsed[key] = value
    return parsed

# Get all records as a list of dicts
raw_responses = worksheet.get_all_records()
responses = [parse_row(row) for row in raw_responses]

# Output as pretty JSON
print(json.dumps(responses, indent=2, ensure_ascii=False)) 