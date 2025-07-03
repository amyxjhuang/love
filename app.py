from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Get the Google Sheet URL from environment variable
SHEET_URL = os.getenv('GOOGLE_SHEET_URL')

app = Flask(__name__)
CORS(app, origins=["*"])  # Allow requests from any origin

def fetch_sheet_data():
    """Fetch data from public Google Sheet URL"""
    try:
        if not SHEET_URL:
            raise Exception("GOOGLE_SHEET_URL environment variable not set")
        
        # Convert to the public JSON endpoint
        sheet_id = SHEET_URL.split('/d/')[1].split('/')[0]
        public_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:json'
        
        response = requests.get(public_url)
        response.raise_for_status()
        
        # Google Sheets returns data wrapped in a function call, we need to extract it
        text = response.text
        json_text = text[47:-2]  # Remove the wrapper
        data = json.loads(json_text)
        
        return data
    except Exception as e:
        print(f"Error fetching sheet data: {e}")
        return None

def process_sheet_data(data):
    """Process the sheet data into the format we need"""
    if not data or 'table' not in data:
        return None
    
    rows = data['table']['rows']
    headers = [col['label'] for col in data['table']['cols']]
    
    # Convert to array of objects
    records = []
    for row in rows:
        record = {}
        for i, cell in enumerate(row['c']):
            if cell and 'f' in cell:
                record[headers[i]] = cell['f']
            else:
                record[headers[i]] = cell['v'] if cell else ''
        records.append(record)
    
    return records

def get_status(records):
    """Get status summary from records"""
    # Find most recent hangout
    hangout_entries = [r for r in records if r.get('Did you hang out (in real life)? ') == 'Yes' and r.get('What day is this for? ')]
    hangout_entries.sort(key=lambda x: x['What day is this for? '], reverse=True)
    
    # Find most recent Minecraft hangout
    minecraft_entries = [r for r in records if r.get('Did you hang out (in real life)? ') == 'Yes' and r.get('What day is this for? ') and 'We played Minecraft' in r.get('Check all that are true for this hangout.', '')]
    minecraft_entries.sort(key=lambda x: x['What day is this for? '], reverse=True)
    
    # Find most recent kiss hangout
    kiss_entries = [r for r in records if r.get('Did you hang out (in real life)? ') == 'Yes' and r.get('What day is this for? ') and ('We held hands and kissed' in r.get('Check all that are true for this hangout.', '') or 'We kissed' in r.get('Check all that are true for this hangout.', ''))]
    kiss_entries.sort(key=lambda x: x['What day is this for? '], reverse=True)
    
    return {
        'last_hangout_date': hangout_entries[0]['What day is this for? '] if hangout_entries else None,
        'last_minecraft_date': minecraft_entries[0]['What day is this for? '] if minecraft_entries else None,
        'last_kiss_date': kiss_entries[0]['What day is this for? '] if kiss_entries else None
    }

def get_last_entries(records):
    """Get last entries for each user"""
    # Separate entries by user
    amy_entries = [r for r in records if r.get('Who is filling this out right now.') == 'Amy']
    michael_entries = [r for r in records if r.get('Who is filling this out right now.') == 'Michael']
    
    # Sort by timestamp (most recent first)
    amy_entries.sort(key=lambda x: x.get('Timestamp', ''), reverse=True)
    michael_entries.sort(key=lambda x: x.get('Timestamp', ''), reverse=True)
    
    return {
        'amy': amy_entries[0] if amy_entries else None,
        'michael': michael_entries[0] if michael_entries else None
    }

def get_memories_and_worries(records):
    """Get all memories and worries from records"""
    memories_and_worries = []
    
    for record in records:
        user = record.get('Who is filling this out right now.', '')
        timestamp = record.get('Timestamp', '')
        date = record.get('What day is this for? ', '')
        
        # Collect good memories
        memory = record.get("What's a good memory from this hangout (or relationship)? ", '')
        if memory and memory.strip():
            memories_and_worries.append({
                'user': user,
                'type': 'memory',
                'text': memory,
                'timestamp': timestamp,
                'date': date
            })
        
        # Collect worries
        worry = record.get("What's something you're worried about? ", '')
        if worry and worry.strip():
            memories_and_worries.append({
                'user': user,
                'type': 'worry',
                'text': worry,
                'timestamp': timestamp,
                'date': date
            })
        
        # Collect "anything else" notes
        other = record.get("Anything else to note?", '')
        if other and other.strip():
            memories_and_worries.append({
                'user': user,
                'type': 'other',
                'text': other,
                'timestamp': timestamp,
                'date': date
            })
    
    # Sort by timestamp (most recent first)
    memories_and_worries.sort(key=lambda x: x['timestamp'], reverse=True)
    return memories_and_worries

@app.route('/')
def home():
    return jsonify({
        "message": "Relationship Dashboard API",
        "endpoints": {
            "/status": "Get status summary only",
            "/last-entries": "Get last entries for each user",
            "/hangout-data": "Get all data (status, last entries, memories, worries)",
            "/test": "Test endpoint"
        }
    })

@app.route('/hangout-data')
def hangout_data():
    try:
        # Fetch data from public sheet
        sheet_data = fetch_sheet_data()
        if not sheet_data:
            return jsonify({"error": "Failed to fetch sheet data"}), 500
        
        # Process the data
        records = process_sheet_data(sheet_data)
        if not records:
            return jsonify({"error": "Failed to process sheet data"}), 500
        
        # Get status summary
        status_data = get_status(records)
        
        # Get last entries for each user
        last_entries_data = get_last_entries(records)
        
        # Get all memories and worries
        memories_and_worries = get_memories_and_worries(records)
        
        # Check if relationship is monogamous
        monogamous = not any(
            'non monogamous' in (record.get('Select all that you feel is true ', '') or '').lower()
            for record in records
        )
        
        return jsonify({
            'status': status_data,
            'last_entries': last_entries_data,
            'memories_and_worries': memories_and_worries,
            'monogamous': monogamous
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status')
def status():
    try:
        sheet_data = fetch_sheet_data()
        if not sheet_data:
            return jsonify({"error": "Failed to fetch sheet data"}), 500
        
        records = process_sheet_data(sheet_data)
        if not records:
            return jsonify({"error": "Failed to process sheet data"}), 500
        
        return jsonify(get_status(records))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/last-entries')
def last_entries():
    try:
        sheet_data = fetch_sheet_data()
        if not sheet_data:
            return jsonify({"error": "Failed to fetch sheet data"}), 500
        
        records = process_sheet_data(sheet_data)
        if not records:
            return jsonify({"error": "Failed to process sheet data"}), 500
        
        return jsonify(get_last_entries(records))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test')
def test():
    return jsonify({
        "message": "API is working!",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# For Vercel deployment
app.debug = True

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 