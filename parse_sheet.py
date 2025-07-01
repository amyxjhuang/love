import gspread
from google.oauth2.service_account import Credentials

# Path to your downloaded service account key
SERVICE_ACCOUNT_FILE = 'amyg-49fcaf834c17.json'

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Authenticate and create the client
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Open the sheet by name or URL
sheet = client.open('Relationship Survey (Responses)').sheet1

# Get all records as a list of dicts
records = sheet.get_all_records()
print(records)
