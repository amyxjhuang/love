from flask import Flask, jsonify
from flask_cors import CORS
from get_current_status import get_recent_hangout, get_recent_minecraft_hangout
import os

app = Flask(__name__)
CORS(app)  # Allow requests from your website

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