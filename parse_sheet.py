import gspread
from google.oauth2.service_account import Credentials

# Path to your downloaded service account key
SERVICE_ACCOUNT_FILE = 'amyhuang-49fcaf834c17.json'

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate and create the client
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1HBrwFrSRBhiRsGPYI7ItChttzdtHFbPuaNCq6LKE15I/edit?gid=724269780#gid=724269780').sheet1
# sheet = client.open('Relationship Survey (Responses)').sheet1

# Get all records as a list of dicts
records = sheet.get_all_records()
print(records)
