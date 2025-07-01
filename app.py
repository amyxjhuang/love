from flask import Flask, jsonify
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from datetime import datetime
from get_current_status import get_recent_hangout, get_recent_minecraft_hangout
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