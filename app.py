from flask import Flask, jsonify
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv
from datetime import datetime
from get_current_status import get_recent_hangout, get_recent_minecraft_hangout, get_status, get_last_entry
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
            "/test": "Test endpoint"
        }
    })


# @app.route('/status')
# def status():
#     try:
#         return jsonify(get_status())
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @app.route('/last-entries')
# def last_entries():
#     try:
#         data = get_last_entry()
#         # Convert datetime objects to strings for JSON serialization
#         if data['amy']:
#             data['amy']['date'] = data['amy']['date'].strftime('%Y-%m-%d %H:%M:%S')
#         if data['michael']:
#             data['michael']['date'] = data['michael']['date'].strftime('%Y-%m-%d %H:%M:%S')
#         return jsonify(data)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @app.route('/all')
# def all_data():
#     try:
#         # Get status summary
#         status_data = get_status()
        
#         # Get last entries for each user
#         last_entries_data = get_last_entry()
        
#         # Convert datetime objects to strings for JSON serialization
#         if last_entries_data['amy']:
#             last_entries_data['amy']['date'] = last_entries_data['amy']['date'].strftime('%Y-%m-%d %H:%M:%S')
#         if last_entries_data['michael']:
#             last_entries_data['michael']['date'] = last_entries_data['michael']['date'].strftime('%Y-%m-%d %H:%M:%S')
        
#         return jsonify({
#             'status': status_data,
#             'last_entries': last_entries_data
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route('/test')
def test():
    return jsonify({
        "message": "API is working!",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# For Vercel deployment
app.debug = True

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 
