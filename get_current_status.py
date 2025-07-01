import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from datetime import datetime

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

def get_recent_hangout():
    # Get all records
    raw_responses = worksheet.get_all_records()
    
    # Filter for responses where they hung out
    hangout_responses = []
    
    for row in raw_responses:
        hangout_field = row.get('Did you hang out (in real life)? ', '')
        date_field = row.get('What day is this for? ', '')
        
        if hangout_field == 'Yes' and date_field:
            try:
                # Parse the date (assuming format like '6/29/2025')
                date_obj = datetime.strptime(date_field, '%m/%d/%Y')
                hangout_responses.append({
                    'date': date_obj,
                    'date_string': date_field,
                    'user': row.get('Who is filling this out right now.', 'Unknown'),
                    'activities': row.get('Check all that are true for this hangout.', '')
                })
            except ValueError:
                print(f"Could not parse date: {date_field}")
                continue
    
    if not hangout_responses:
        print("No hangout responses found!")
        return None
    
    # Sort by date (most recent first)
    hangout_responses.sort(key=lambda x: x['date'], reverse=True)
    
    # Get the most recent
    most_recent = hangout_responses[0]
    
    print(f"Most recent hangout: {most_recent['date_string']}")
    print(f"User: {most_recent['user']}")
    print(f"Good memory: {most_recent['good_memory']}")
    print(f"Activities: {most_recent['activities']}")
    
    return most_recent

def get_recent_minecraft_hangout():
    # Get all records
    raw_responses = worksheet.get_all_records()
    
    # Filter for responses where they hung out and played Minecraft
    minecraft_responses = []
    
    for row in raw_responses:
        hangout_field = row.get('Did you hang out (in real life)? ', '')
        date_field = row.get('What day is this for? ', '')
        activities_field = row.get('Check all that are true for this hangout.', '')
        
        if hangout_field == 'Yes' and date_field and 'We played Minecraft' in activities_field:
            try:
                # Parse the date (assuming format like '6/29/2025')
                date_obj = datetime.strptime(date_field, '%m/%d/%Y')
                minecraft_responses.append({
                    'date': date_obj,
                    'date_string': date_field,
                    'user': row.get('Who is filling this out right now.', 'Unknown'),
                    'activities': activities_field
                })
            except ValueError:
                print(f"Could not parse date: {date_field}")
                continue
    
    if not minecraft_responses:
        print("No Minecraft hangout responses found!")
        return None
    
    # Sort by date (most recent first)
    minecraft_responses.sort(key=lambda x: x['date'], reverse=True)
    
    # Get the most recent
    most_recent = minecraft_responses[0]
    
    print(f"Most recent Minecraft hangout: {most_recent['date_string']}")
    print(f"User: {most_recent['user']}")
    print(f"Good memory: {most_recent['good_memory']}")
    print(f"Activities: {most_recent['activities']}")
    
    return most_recent

if __name__ == "__main__":
    print("=== Most Recent Hangout ===")
    x = get_recent_hangout()
    print(x)
    print("\n=== Most Recent Minecraft Hangout ===")
    get_recent_minecraft_hangout() 