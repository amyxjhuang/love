from flask import Flask, jsonify
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Handle service account for Vercel
SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON')
if SERVICE_ACCOUNT_JSON:
    # If the JSON is stored as an environment variable, write it to a file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(SERVICE_ACCOUNT_JSON)
        SERVICE_ACCOUNT_FILE = f.name
else:
    SERVICE_ACCOUNT_FILE = 'amyhuang-49fcaf834c17.json'

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate and create the client
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Get the Google Sheet URL from environment variable
SHEET_URL = os.getenv('GOOGLE_SHEET_URL')
worksheet = client.open_by_url(SHEET_URL).sheet1

# Define the hangout functions
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
                    'good_memory': row.get("What's a good memory from this hangout (or relationship)? ", ''),
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
                    'good_memory': row.get("What's a good memory from this hangout (or relationship)? ", ''),
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
    
    return most_recent

app = Flask(__name__)
CORS(app, origins=["*"])  # Allow requests from any origin

@app.route('/')
def home():
    return jsonify({
        "message": "Relationship Dashboard API",
        "endpoints": {
            "/hangout": "Get most recent hangout",
            "/minecraft": "Get most recent Minecraft hangout",
            "/all": "Get both hangout and Minecraft data"
        }
    })

@app.route('/hangout')
def hangout():
    try:
        data = get_recent_hangout()
        if data:
            # Convert datetime to string for JSON serialization
            data['date'] = data['date'].strftime('%Y-%m-%d')
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/minecraft')
def minecraft():
    try:
        data = get_recent_minecraft_hangout()
        if data:
            # Convert datetime to string for JSON serialization
            data['date'] = data['date'].strftime('%Y-%m-%d')
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/all')
def all_data():
    try:
        recent_hangout = get_recent_hangout()
        recent_minecraft = get_recent_minecraft_hangout()
        
        # Convert datetime objects to strings
        if recent_hangout:
            recent_hangout['date'] = recent_hangout['date'].strftime('%Y-%m-%d')
        if recent_minecraft:
            recent_minecraft['date'] = recent_minecraft['date'].strftime('%Y-%m-%d')
        
        return jsonify({
            'recent_hangout': recent_hangout,
            'recent_minecraft': recent_minecraft
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# For Vercel deployment
app.debug = True

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 