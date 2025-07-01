import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

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

# Get the Google Sheet URL from the environment variable
SHEET_URL = os.getenv('GOOGLE_SHEET_URL')

sheet = client.open_by_url(SHEET_URL).sheet1
# sheet = client.open('Relationship Survey (Responses)').sheet1

# Get all records as a list of dicts
records = sheet.get_all_records()
print(records)
