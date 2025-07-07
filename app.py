from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import resend

# Load environment variables
load_dotenv()

# Get the Google Sheet URL from environment variable
SHEET_URL = os.getenv('GOOGLE_SHEET_URL')
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'onboarding@resend.dev')
EMAIL_TO = os.getenv('EMAIL_TO', 'fineshyts@michaelamy5ever.com')

# Initialize Resend
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

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

def process_records(records):
    """Process and sort all records for efficient access"""
    # Sort records by timestamp (most recent first)
    sorted_records = sorted(records, key=lambda x: x.get('Timestamp', ''), reverse=True)
    
    # Separate entries by user (already sorted by timestamp)
    amy_entries = [r for r in sorted_records if r.get('Who is filling this out right now.') == 'Amy']
    michael_entries = [r for r in sorted_records if r.get('Who is filling this out right now.') == 'Michael']
    
    # Get hangout entries sorted by date (most recent first)
    hangout_entries = [r for r in sorted_records if r.get('Did you hang out (in real life)? ') == 'Yes' and r.get('What day is this for? ')]
    hangout_entries.sort(key=lambda x: x['What day is this for? '], reverse=True)
    
    # Get Minecraft hangout entries sorted by date
    minecraft_entries = [r for r in sorted_records if r.get('Did you hang out (in real life)? ') == 'Yes' and r.get('What day is this for? ') and 'We played Minecraft' in r.get('Check all that are true for this hangout.', '')]
    minecraft_entries.sort(key=lambda x: x['What day is this for? '], reverse=True)
    
    # Get kiss hangout entries sorted by date
    kiss_entries = [r for r in sorted_records if r.get('Did you hang out (in real life)? ') == 'Yes' and r.get('What day is this for? ') and ('We held hands and kissed' in r.get('Check all that are true for this hangout.', '') or 'We kissed' in r.get('Check all that are true for this hangout.', ''))]
    kiss_entries.sort(key=lambda x: x['What day is this for? '], reverse=True)
    
    # Collect memories and worries (already sorted by timestamp from sorted_records)
    memories_and_worries = []
    for record in sorted_records:
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
    
    return {
        'sorted_records': sorted_records,
        'amy_entries': amy_entries,
        'michael_entries': michael_entries,
        'hangout_entries': hangout_entries,
        'minecraft_entries': minecraft_entries,
        'kiss_entries': kiss_entries,
        'memories_and_worries': memories_and_worries
    }

def get_status(processed_data):
    """Get status summary from processed data"""
    return {
        'is_long_distance': processed_data['sorted_records'][0]['Are you long distance right now?'] if processed_data['sorted_records'] else None,
        'last_hangout_date': processed_data['hangout_entries'][0]['What day is this for? '] if processed_data['hangout_entries'] else None,
        'last_minecraft_date': processed_data['minecraft_entries'][0]['What day is this for? '] if processed_data['minecraft_entries'] else None,
        'last_kiss_date': processed_data['kiss_entries'][0]['What day is this for? '] if processed_data['kiss_entries'] else None
    }

def get_last_entries(processed_data):
    """Get last entries for each user from processed data"""
    return {
        'amy': processed_data['amy_entries'][0] if processed_data['amy_entries'] else None,
        'michael': processed_data['michael_entries'][0] if processed_data['michael_entries'] else None
    }

def get_memories_and_worries(processed_data):
    """Get memories and worries from processed data"""
    return processed_data['memories_and_worries']

def generate_weekly_email(processed_data):
    """Generate weekly email content"""
    status = get_status(processed_data)
    last_entries = get_last_entries(processed_data)
    memories = get_memories_and_worries(processed_data)
    
    # Get recent memories (last 7 days or last 5 entries)
    recent_memories = memories[:5] if memories else []
    
    # Basic email template - customize this later
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #f595eb 0%, #ffa500 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
            .section {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
            .memory {{ margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #f595eb; }}
            .date {{ color: #666; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>💕 Weekly Relationship Update</h1>
            <p>{datetime.now().strftime('%B %d, %Y')}</p>
        </div>
        
        <div class="section">
            <h2>📊 Status Summary</h2>
            <p><strong>Last Hangout:</strong> {status.get('last_hangout_date', 'No recent hangouts')}</p>
            <p><strong>Last Minecraft Day:</strong> {status.get('last_minecraft_date', 'No recent Minecraft')}</p>
            <p><strong>Last Kiss:</strong> {status.get('last_kiss_date', 'No recent kisses')}</p>
        </div>
        
        <div class="section">
            <h2>👥 Recent Survey Responses</h2>
            {f'<p><strong>Amy:</strong> Relationship strength: {last_entries["amy"].get("How strong do you think our relationship is?", "N/A")}/5</p>' if last_entries.get('amy') else '<p>No recent response from Amy</p>'}
            {f'<p><strong>Michael:</strong> Relationship strength: {last_entries["michael"].get("How strong do you think our relationship is?", "N/A")}/5</p>' if last_entries.get('michael') else '<p>No recent response from Michael</p>'}
        </div>
        
        <div class="section">
            <h2>💭 Recent Memories & Thoughts</h2>
            {''.join([f'<div class="memory"><strong>{memory["user"]}</strong> ({memory["type"]}): {memory["text"]}<div class="date">{memory["date"]}</div></div>' for memory in recent_memories]) if recent_memories else '<p>No recent memories recorded</p>'}
        </div>
        
        <div class="section">
            <p style="text-align: center; color: #666;">
                💕 Keep the love alive! 💕
            </p>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_weekly_email():
    """Send weekly email with relationship updates"""
    try:
        if not RESEND_API_KEY:
            print("RESEND_API_KEY not set")
            return False
        
        print(f"Using API key: {RESEND_API_KEY[:10]}...")
        print(f"From email: {EMAIL_FROM}")
        print(f"To emails: {EMAIL_TO}")
            
        # Fetch and process data
        sheet_data = fetch_sheet_data()
        if not sheet_data:
            print("Failed to fetch sheet data")
            return False
            
        records = process_sheet_data(sheet_data)
        if not records:
            print("Failed to process sheet data")
            return False
            
        processed_data = process_records(records)
        
        # Generate email content
        html_content = generate_weekly_email(processed_data)
        
        # Send email
        email_to_list = [email.strip() for email in EMAIL_TO.split(',')]
        
        print(f"Sending email to: {email_to_list}")
        
        response = resend.Emails.send({
            "from": EMAIL_FROM,
            "to": email_to_list,
            "subject": f"💕 Weekly Relationship Update - {datetime.now().strftime('%B %d, %Y')}",
            "html": html_content
        })
        
        print(f"Email sent successfully: {response['id']}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

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
        
        # Process and sort all records once
        processed_data = process_records(records)
        
        # Get status summary
        status_data = get_status(processed_data)
        
        # Get last entries for each user
        last_entries_data = get_last_entries(processed_data)
        
        # Get all memories and worries
        memories_and_worries = get_memories_and_worries(processed_data)
        
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
        
        # Process and sort all records once
        processed_data = process_records(records)
        
        return jsonify(get_status(processed_data))
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
        
        # Process and sort all records once
        processed_data = process_records(records)
        
        return jsonify(get_last_entries(processed_data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test')
def test():
    return jsonify({
        "message": "API is working!",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/send-email')
def trigger_email():
    """Manually trigger weekly email (for testing)"""
    try:
        success = send_weekly_email()
        if success:
            return jsonify({
                "message": "Weekly email sent successfully!",
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return jsonify({"error": "Failed to send email"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test-email')
def test_simple_email():
    print(f"Using API key: {RESEND_API_KEY[:10]}...")
    print(f"From email: {EMAIL_FROM}")
    print(f"To emails: {EMAIL_TO}")
        
    """Send a simple test email"""
    try:
        if not RESEND_API_KEY:
            return jsonify({"error": "RESEND_API_KEY not set"}), 500
        
        email_to_list = [email.strip() for email in EMAIL_TO.split(',')]
        print(f"Sending email to: {email_to_list}")
        response = resend.Emails.send({
            "from": EMAIL_FROM,
            "to": email_to_list,
            "subject": "🧪 Test Email from Relationship Dashboard",
            "html": "<h1>Test Email</h1><p>If you receive this, the email setup is working!</p>"
        })
        
        return jsonify({
            "message": "Test email sent successfully!",
            "id": response['id']
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/face-match', methods=['POST'])
def face_match():
    """Compare uploaded face embeddings with stored reference embeddings"""
    try:
        from flask import request
        import numpy as np
        
        # Get the face data from the request
        data = request.get_json()
        if not data or 'faces' not in data:
            return jsonify({"error": "No face data provided"}), 400
        
        uploaded_faces = data['faces']
        if not uploaded_faces:
            return jsonify({"error": "No faces detected in uploaded image"}), 400
        
        # For now, let's use a simple reference embedding
        # You can store this in an environment variable or database
        reference_embedding = [
            100.0, 100.0,  # Keypoint 1 (x, y)
            80.0, 80.0,    # Keypoint 2 (x, y)
            120.0, 80.0,   # Keypoint 3 (x, y)
            90.0, 120.0,   # Keypoint 4 (x, y)
            110.0, 120.0   # Keypoint 5 (x, y)
        ]
        
        best_match = None
        best_similarity = 0.0
        
        # Compare each uploaded face with the reference
        for face in uploaded_faces:
            embedding = face.get('embedding', [])
            if len(embedding) >= len(reference_embedding):
                # Pad or truncate to match reference length
                embedding = embedding[:len(reference_embedding)]
                while len(embedding) < len(reference_embedding):
                    embedding.append(0.0)
                
                # Calculate cosine similarity
                embedding_np = np.array(embedding)
                reference_np = np.array(reference_embedding)
                
                # Normalize vectors
                embedding_norm = np.linalg.norm(embedding_np)
                reference_norm = np.linalg.norm(reference_np)
                
                if embedding_norm > 0 and reference_norm > 0:
                    similarity = np.dot(embedding_np, reference_np) / (embedding_norm * reference_norm)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = face
        
        # Determine if it's a match (threshold can be adjusted)
        match_threshold = 0.7
        is_match = best_similarity >= match_threshold
        
        return jsonify({
            "match": is_match,
            "similarity": best_similarity,
            "message": f"Best similarity: {best_similarity:.3f} (threshold: {match_threshold})",
            "face_count": len(uploaded_faces),
            "best_face_confidence": best_match['confidence'] if best_match else 0.0
        })
        
    except Exception as e:
        print(f"Error in face matching: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/gift-verify', methods=['POST'])
def gift_verify():
    """Verify password and return gift information"""
    try:
        from flask import request
        
        # Get the password from the request
        data = request.get_json()
        if not data or 'password' not in data:
            return jsonify({"error": "No password provided"}), 400
        
        submitted_password = data['password'].strip()
        
        # Set your password here (you can also use environment variable)
        correct_password = os.getenv('GIFT_PASSWORD')
        print(f"Correct password: {correct_password}")
        if submitted_password == correct_password:
            # Return gift information
            gift_data = {
                "unlocked": True,
                "message": "correct password.",
                "gift_content": {
                    "title": "happy 5 months!!!! ",
                    "subtitle": "",
                    "sections": [
                        {
                            "type": "message",
                            "content": "placeholder"
                        },
                        {
                            "type": "preview_images",
                            "title": "",
                            "images": [
                                {
                                    "src": "/gift-assets/michael-preview.png",
                                    "alt": "Michael Preview"
                                },
                                {
                                    "src": "/gift-assets/amy-preview.png", 
                                    "alt": "Amy Preview"
                                }
                            ]
                        },
                        {
                            "type": "download_section",
                            "title": "download here",
                            "description": "Choose your preferred style:",
                            "downloads": [
                                {
                                    "name": "Download Classic",
                                    "file": "/gift-assets/michael_classic.png",
                                    "filename": "michael_classic.png"
                                },
                                {
                                    "name": "Download Slim",
                                    "file": "/gift-assets/michael_slim.png",
                                    "filename": "michael_slim.png"
                                }
                            ]
                        }
                    ],
                }
            }
            return jsonify(gift_data)
        else:
            return jsonify({
                "unlocked": False,
                "message": "❌ Wrong password! Do you even know anything about anything?",
                "hint": ""
            }), 401
        
    except Exception as e:
        print(f"Error in gift verification: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/gift-assets/<path:filename>')
def serve_gift_assets(filename):
    """Serve gift asset files"""
    try:
        from flask import send_from_directory
        return send_from_directory('gift-assets', filename)
    except Exception as e:
        print(f"Error serving gift asset {filename}: {e}")
        return jsonify({"error": "File not found"}), 404

# For Vercel deployment
app.debug = True

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 