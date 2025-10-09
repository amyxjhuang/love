from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import resend
from datetime import datetime, timedelta

import resend.emails

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
        # print(response.text)
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

def parse_timestamp(ts):
    # Try to parse common formats, fallback to string for broken/missing values
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%y %H:%M:%S", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(ts, fmt)
        except Exception:
            continue
    return datetime.min  # Put unparseable/missing dates at the end

def parse_date(date_str):
    """Parse date strings like '6/29/25' or '6/29/2025'"""
    if not date_str:
        return datetime.min
    
    try:
        # Handle different date formats
        if '/' in date_str:
            parts = date_str.split('/')
            month = int(parts[0])
            day = int(parts[1])
            year = int(parts[2])
            
            # Handle 2-digit years
            if year < 100:
                year += 2000
                
            return datetime(year, month, day)
        else:
            return datetime.min
    except Exception:
        return datetime.min

def process_records(records):
    """Process and sort all records for efficient access"""
    # Sort records by date (most recent first), then by timestamp as tiebreaker
    sorted_records = sorted(records, key=lambda x: (parse_date(x.get('What day is this for? ', '')).timestamp(), parse_timestamp(x.get('Timestamp', '')).timestamp()), reverse=True)
    print([parse_date(r.get('What day is this for? ', '')).timestamp() for r in sorted_records])
    # Separate entries by user (already sorted by timestamp)
    amy_entries = [r for r in sorted_records if r.get('Who is filling this out right now.') == 'Amy']
    michael_entries = [r for r in sorted_records if r.get('Who is filling this out right now.') == 'Michael']
    
    # Get hangout entries sorted by date (most recent first)
    hangout_entries = [r for r in sorted_records if r.get('Did you hang out (in real life)? ') == 'Yes' and r.get('What day is this for? ')]
    # hangout_entries.sort(key=lambda x: x['What day is this for? '], reverse=True)
    
    # Get Minecraft hangout entries sorted by date
    minecraft_entries = [r for r in sorted_records if r.get('Did you hang out (in real life)? ') == 'Yes' and r.get('What day is this for? ') and 'We played Minecraft' in r.get('Check all that are true for this hangout.', '')]
    # minecraft_entries.sort(key=lambda x: x['What day is this for? '], reverse=True)
    
    # Get kiss hangout entries sorted by date
    kiss_entries = [r for r in sorted_records if r.get('Did you hang out (in real life)? ') == 'Yes' and ('We held hands and kissed' in r.get('Check all that are true for this hangout.', '') or 'kissed' in r.get('Check all that are true for this hangout.', ''))]
    # kiss_entries.sort(key=lambda x: x['What day is this for? '], reverse=True)
    print(len(kiss_entries), [r['What day is this for? '] for r in kiss_entries])
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
    print(processed_data['sorted_records'][0])

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

def get_30_day_trends(processed_data):
    """Get 30-day trend data for graphing"""
    from datetime import datetime, timedelta
    
    # Get records from the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Filter records from last 30 days
    recent_records = []
    for record in processed_data['sorted_records']:
        record_date = get_date_from_record(record)
        if record_date and record_date >= thirty_days_ago:
            recent_records.append(record)
    
    # Create a dictionary to store daily data
    daily_data = {}
    for record in recent_records:
        date_key = get_date_from_record(record).strftime('%Y-%m-%d')
        if date_key not in daily_data:
            daily_data[date_key] = {
                'amy': None,
                'michael': None
            }
        
        user = record.get('Who is filling this out right now.', '')
        if user in ['Amy', 'Michael']:
            daily_data[date_key][user.lower()] = record
    
    # Generate complete 30-day dataset (backfill missing days)
    dates = []
    relationship_strength = []
    amy_stress = []
    michael_stress = []
    hangouts = []
    kisses = []
    minecraft = []
    crashouts_or_arguments = []
    
    # Start from 30 days ago and go to today
    current_date = thirty_days_ago
    while current_date <= datetime.now():
        date_str = current_date.strftime('%Y-%m-%d')
        dates.append(date_str)
        
        day_data = daily_data.get(date_str, {'amy': None, 'michael': None})
        
        # Get relationship strength (average of both users if available)
        amy_strength = None
        michael_strength = None
        if day_data['amy']:
            try:
                amy_strength = int(day_data['amy'].get('How strong do you think our relationship is?', '0') or '0')
            except:
                amy_strength = 0
        if day_data['michael']:
            try:
                michael_strength = int(day_data['michael'].get('How strong do you think our relationship is?', '0') or '0')
            except:
                michael_strength = 0
        
        # Average strength (or use single value if only one available)
        if amy_strength is not None and michael_strength is not None:
            avg_strength = (amy_strength + michael_strength) / 2
        elif amy_strength is not None:
            avg_strength = amy_strength
        elif michael_strength is not None:
            avg_strength = michael_strength
        else:
            avg_strength = None
        relationship_strength.append(avg_strength)
        
        # Get stress levels
        amy_stress_val = None
        michael_stress_val = None
        if day_data['amy']:
            try:
                amy_stress_val = int(day_data['amy'].get('How stressed are you about things outside of our relationship? ', '0') or '0')
            except:
                amy_stress_val = 0
        if day_data['michael']:
            try:
                michael_stress_val = int(day_data['michael'].get('How stressed are you about things outside of our relationship? ', '0') or '0')
            except:
                michael_stress_val = 0
        
        amy_stress.append(amy_stress_val)
        michael_stress.append(michael_stress_val)
        
        # Check for hangout activities
        hangout_activities = set()
        kiss_day = 0
        minecraft_day = 0
        hangout_day = 0
        crashout_or_argument_day = 0
        
        for user_data in [day_data['amy'], day_data['michael']]:
            if user_data and user_data.get('Did you hang out (in real life)? ') == 'Yes':
                hangout_day = 1
                activities = user_data.get('Check all that are true for this hangout.', '')
                if activities:
                    hangout_activities.update(activities.split(','))
        
        if 'We held hands and kissed' in hangout_activities or 'kissed' in str(hangout_activities):
            kiss_day = 1
        if 'We played Minecraft' in hangout_activities:
            minecraft_day = 1
        
        # Check for crashouts or arguments
        for user_data in [day_data['amy'], day_data['michael']]:
            if user_data:
                crashout_key = "Did you have any crash outs about us? \n\nSomething counts as a crash out if you spent >30 minutes worrying about the relationship, or had a bad thought that lasted multiple days. "
                argument_key = "Did we argue? \n\nSomething counts as an argument if one party felt anger about something, and brought it up, and it was not immediately resolved. "
                
                if (user_data.get(crashout_key, '') == 'Yes' or 
                    user_data.get(argument_key, '') == 'Yes'):
                    crashout_or_argument_day = 1
                    break
        
        hangouts.append(hangout_day)
        kisses.append(kiss_day)
        minecraft.append(minecraft_day)
        crashouts_or_arguments.append(crashout_or_argument_day)
        
        current_date += timedelta(days=1)
    
    return {
        'dates': dates,
        'relationship_strength': relationship_strength,
        'amy_stress': amy_stress,
        'michael_stress': michael_stress,
        'hangouts': hangouts,
        'kisses': kisses,
        'minecraft': minecraft,
        'crashouts_or_arguments': crashouts_or_arguments
    }

def is_record_from_last_7_days(record):
    seven_days_ago = datetime.now() - timedelta(days=7)

    date_str = record.get('What day is this for? ', '')
    if not date_str:
        return False
    
    # Use the parse_date function for consistency
    date = parse_date(date_str)
    return date >= seven_days_ago

            
def get_date_from_record(record):
    # print(f"get_date_from_record: {record.get('What day is this for? ', 'No date')}")
    date_str = record.get('What day is this for? ', '')
    if not date_str:
        return None

    # Use the parse_date function for consistency
    parsed_date = parse_date(date_str)
    return parsed_date if parsed_date != datetime.min else None

def generate_weekly_stats_from_data(processed_data):

    sorted_records = processed_data['sorted_records']
    amy_entries = processed_data['amy_entries']
    michael_entries = processed_data['michael_entries']
    hangout_entries = processed_data['hangout_entries']
    minecraft_entries = processed_data['minecraft_entries']
    kiss_entries = processed_data['kiss_entries']
    memories_and_worries = processed_data['memories_and_worries']

    print("STARTING BACKFILL FOR AMY")
    amy_records_from_last_7_days = backfill_missing_dates_for_week(amy_entries[:9])
    print("STARTING BACKFILL FOR MICHAEL")
    michael_records_from_last_7_days = backfill_missing_dates_for_week(michael_entries[:9])
    print("FINISHED BACKFILL")

    return get_data_from_backfilled_records(michael_records_from_last_7_days, amy_records_from_last_7_days)

def backfill_missing_dates_for_week(records):
    records = records[::-1]
    seven_days_ago = datetime.now() - timedelta(days=7)
    print(f"7 days ago: {seven_days_ago}")
    last_record = records[0]
    for record in records:
        record_date = get_date_from_record(record)
        if record_date >= seven_days_ago:
            # Once we reach 7 days ago, stop
            break 
        last_record = record

    last_record_date = get_date_from_record(last_record)
    print(f"last record date: {last_record_date}")
    backfilled_records = []
    last_date = seven_days_ago
    curr_record = records.pop(0)

    while last_date <  datetime.now():

        while get_date_from_record(curr_record) < last_date - timedelta(days=1) and records:
            curr_record = records.pop(0)

        print(f"curr_record: {get_date_from_record(curr_record)}")
        # print(get_date_from_record(curr_record), last_date)
        if get_date_from_record(curr_record).month == last_date.month and get_date_from_record(curr_record).day == last_date.day:
            print(f"{get_date_from_record(curr_record)} found")
            record_to_append = curr_record.copy()
            last_record = curr_record
            # print(record_to_append.get("Did you hang out (in real life)? ", "No, everything is good"))
            # print(record_to_append.get("How strong do you think our relationship is?", "No, everything is good"))
            # print(record_to_append['Did you have any crash outs about us? \n\nSomething counts as a crash out if you spent >30 minutes worrying about the relationship, or had a bad thought that lasted multiple days. '])
        else:
            print(f"backfilling {last_date}")
            # print(last_record)
            record_to_append = {}
            record_to_append['What day is this for? '] = last_date.strftime("%m/%d/%Y")
            record_to_append['Did you hang out (in real life)? '] = 'No'
            record_to_append['Select all that you feel is true '] = ''
            record_to_append['Who is filling this out right now.'] = last_record.get('Who is filling this out right now.', '')
            record_to_append['Timestamp'] = last_record.get('Timestamp', '')
            record_to_append['Are you long distance right now?'] = last_record.get('Are you long distance right now?', '')
            record_to_append['How strong do you think our relationship is?'] = last_record.get('How strong do you think our relationship is?', '')
            record_to_append['How stressed are you about things outside of our relationship? '] = last_record.get('How stressed are you about things outside of our relationship? ', '')            # print(f"{get_date_from_record(record_to_append)} backfilled")
            record_to_append['Do you still like me? '] = last_record.get('Do you still like me? ')
            record_to_append['Did we argue? \n\nSomething counts as an argument if one party felt anger about something, and brought it up, and it was not immediately resolved. '] = 'No, everything is good.'
            record_to_append['Did you have any crash outs about us? \n\nSomething counts as a crash out if you spent >30 minutes worrying about the relationship, or had a bad thought that lasted multiple days. '] = 'No, everything is good.'
        backfilled_records.append(record_to_append)
        last_date += timedelta(days=1)

    return backfilled_records    

def get_data_from_backfilled_records(backfilled_records_michael, backfilled_records_amy):
    """Get data from backfilled records"""
    num_hangouts = 0 
    num_crashouts_or_arguments = 0 
    num_calls = 0
    num_kisses = 0 
    num_minecraft = 0 
    strength_levels = [] 
    amy_stress_levels = []
    michael_stress_levels = [] 
    days_long_distance = 0
    num_sleepovers = 0
    for i in range(7):
        michael_record = backfilled_records_michael[i]
        amy_record = backfilled_records_amy[i]
        if michael_record.get('Did you hang out (in real life)? ') == 'Yes' or amy_record.get('Did you hang out (in real life)? ') == 'Yes':
            num_hangouts += 1

            hangout_activity_list = set()
            print(michael_record.get("Check all that are true for this hangout.", "none").split(','))
            # print(michael_record["Check all that are true for this hangout."])
            hangout_activity_list.update(michael_record.get("Check all that are true for this hangout.", "").split(",")) 
            hangout_activity_list.update(amy_record.get("Check all that are true for this hangout.", "").split(",")) 
            if hangout_activity_list:
                if ' We held hands and kissed' in hangout_activity_list:
                    num_kisses += 1
                if 'We played Minecraft' in hangout_activity_list:
                    num_minecraft += 1
                if ' We had a sleepover' in hangout_activity_list:
                    num_sleepovers += 1
        if michael_record.get('Are you long distance right now?') == 'Yes' or amy_record.get('Are you long distance right now?') == 'Yes':
            days_long_distance += 1
        crashout_key = "Did you have any crash outs about us? \n\nSomething counts as a crash out if you spent >30 minutes worrying about the relationship, or had a bad thought that lasted multiple days. "
        argument_key = "Did we argue? \n\nSomething counts as an argument if one party felt anger about something, and brought it up, and it was not immediately resolved. "
        had_crashout_or_argument = 'Yes' in (michael_record.get(crashout_key, "") + amy_record.get(crashout_key, "") + michael_record.get(argument_key, "") + amy_record.get(argument_key, ""))
        if had_crashout_or_argument:
            num_crashouts_or_arguments += 1
        # if michael_record.get('Did you hang out (in real life)? ') == 'Yes' and michael_record.get('Check all that are true for this hangout.', '').lower() == 'kiss':
        #     num_kisses += 1
        # if michael_record.get('Did you hang out (in real life)? ') == 'Yes' and michael_record.get('Check all that are true for this hangout.', '').lower() == 'minecraft':
        #     num_minecraft += 1

        strength_levels.append(michael_record.get('How strong do you think our relationship is?', '5'))
        strength_levels.append(amy_record.get('How strong do you think our relationship is?', '5'))
        amy_stress_levels.append(amy_record.get('How stressed are you about things outside of our relationship? ', '1'))
        michael_stress_levels.append(michael_record.get('How stressed are you about things outside of our relationship? ', '1'))
        # if michael_record.get('Did you hang out (in real life)? ') == 'Yes' and michael_record.get('Check all that are true for this hangout.', '').lower() == 'kiss':
   
    print(michael_stress_levels)
    print(amy_stress_levels)
    print(strength_levels)
    average_michael_stress = sum(int(level) for level in michael_stress_levels) / len(michael_stress_levels)
    average_amy_stress = sum(int(level) for level in amy_stress_levels) / len(amy_stress_levels)
    average_strength = sum(int(level) for level in strength_levels) / len(strength_levels)
    print(f"average_michael_stress: {average_michael_stress}")
    print(f"average_amy_stress: {average_amy_stress}")
    print(f"average_strength: {average_strength}")
    print(f"num_hangouts: {num_hangouts}")
    print(f"num_sleepovers: {num_sleepovers}")
    print(f"num_kisses: {num_kisses}")
    print(f"num_minecraft: {num_minecraft}")
    print(f"num_crashouts_or_arguments: {num_crashouts_or_arguments}")
    print(f"num_long_distance: {days_long_distance}")
    return {
        'michael_stress_levels': michael_stress_levels,
        'amy_stress_levels': amy_stress_levels,
        'average_strength': average_strength,
        'num_hangouts': num_hangouts,
        'num_sleepovers': num_sleepovers,
        'num_kisses': num_kisses,
        'num_minecraft': num_minecraft,
        'num_crashouts_or_arguments': num_crashouts_or_arguments,
        'num_long_distance': days_long_distance,
    }

def generate_weekly_email(data):
    """Generate weekly email content"""
    michael_stress_levels = data['michael_stress_levels']
    amy_stress_levels = data['amy_stress_levels']
    average_strength = data['average_strength']
    num_hangouts = data['num_hangouts']
    num_sleepovers = data['num_sleepovers']
    num_kisses = data['num_kisses']
    num_minecraft = data['num_minecraft']
    num_crashouts_or_arguments = data['num_crashouts_or_arguments']
    num_long_distance = data['num_long_distance']
    
    # Calculate averages
    average_michael_stress = sum(int(level) for level in michael_stress_levels) / len(michael_stress_levels)
    average_amy_stress = sum(int(level) for level in amy_stress_levels) / len(amy_stress_levels)
    
    # Generate simple stress level graph
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    stress_graph_html = ""
    
    for i, day in enumerate(days):
        michael_stress = int(michael_stress_levels[i]) if i < len(michael_stress_levels) else 0
        amy_stress = int(amy_stress_levels[i]) if i < len(amy_stress_levels) else 0
        
        # Create simple bar representation
        michael_bars = "█" * michael_stress
        amy_bars = "█" * amy_stress
        
        stress_graph_html += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{day}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; color: #ffa500; font-family: monospace;">{michael_bars} ({michael_stress}/5)</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; color: #f595eb; font-family: monospace;">{amy_bars} ({amy_stress}/5)</td>
        </tr>
        """
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .stats {{ margin: 20px 0; }}
            .stress-graph {{ margin: 30px 0; }}
            table {{ border-collapse: collapse; width: 100%; max-width: 600px; margin: 0 auto; }}
            th {{ background-color: #f5f5f5; padding: 12px; border: 1px solid #ddd; text-align: center; }}
            .link {{ margin: 10px 0; }}
            .link a {{ color: #007bff; text-decoration: none; }}
            .link a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Weekly Relationship Update</h1>
            <p>Week of {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
        
        <div class="stats">
            <h2>Weekly Summary</h2>
            <p><strong>Hangouts:</strong> {num_hangouts} days</p>
            <p><strong>Sleepovers:</strong> {num_sleepovers}</p>
            <p><strong>Kisses:</strong> {num_kisses}</p>
            <p><strong>Minecraft sessions:</strong> {num_minecraft}</p>
            <p><strong>Arguments/Crashouts:</strong> {num_crashouts_or_arguments}</p>
            <p><strong>Long distance days:</strong> {num_long_distance}</p>
            <p><strong>Average relationship strength:</strong> {average_strength:.1f}/5</p>
        </div>
        
        <div class="stress-graph">
            <h2>😰 Stress Levels This Week</h2>
            <p><em>How stressed are you about things outside of our relationship? (1-5 scale)</em></p>
            <table>
                <thead>
                    <tr>
                        <th>Day</th>
                        <th>Michael's Stress</th>
                        <th>Amy's Stress</th>
                    </tr>
                </thead>
                <tbody>
                    {stress_graph_html}
                </tbody>
            </table>
            <p style="text-align: center; margin-top: 20px;">
                <strong>Average Stress:</strong> Michael: {average_michael_stress:.1f}/5 | Amy: {average_amy_stress:.1f}/5
            </p>
        </div>
        
        <div class="link">
            <a href="https://www.michaelamy5ever.com">MichaelAmy5Ever.com</a>
        </div>
        <div class="link">
            <a href="https://docs.google.com/forms/d/e/1FAIpQLScGEZqs93k0rtR1EhohvWi7JaMpLOPAKRik7_WWHgce-F4gfg/viewform">📝 Fill Out Daily Survey</a>
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
        weekly_data = generate_weekly_stats_from_data(processed_data)
        html_content = generate_weekly_email(weekly_data)
        
        # Send email
        email_to_list = [email.strip() for email in EMAIL_TO.split(',')]
        
        print(f"Sending email to: {email_to_list}")
        print(f"API key (first 10 chars): {RESEND_API_KEY[:10] if RESEND_API_KEY else 'None'}...")
        print(f"HTML content length: {len(html_content)} characters")
        
        try:

            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "God <onboarding@resend.dev>",  # must match verified domain
                    "to": email_to_list,
                    "subject": f"[TESTING]VERY IMPORTANT: Weekly Relationship Update - {datetime.now().strftime('%B %d, %Y')}",
                    "html": html_content
                }
            )

            # response = resend.emails.send({
            #     "from": EMAIL_FROM,
            #     "to": email_to_list,
            #     "subject": f"[TESTING]VERY IMPORTANT: Weekly Relationship Update - {datetime.now().strftime('%B %d, %Y')}",
            #     "html": html_content
            # })
            
            print(response.json())
            return response.json()
        except resend.exceptions.ResendError as e:
            print(f"Resend API Error: {e}")
            print(f"Error details: {getattr(e, 'message', 'No message')}")
            print(f"Error code: {getattr(e, 'code', 'No code')}")
            raise
        
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
            "/test": "Test endpoint",
            "/send-email": "Send weekly email",
            "/test-email": "Test email endpoint",
            "/face-match": "Face matching endpoint",
            "/gift-verify": "Gift verification endpoint",
            "/gift-assets/<path:filename>": "Gift asset endpoint"
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
        
        # Get 30-day trend data
        trend_data = get_30_day_trends(processed_data)
        
        # Check if relationship is monogamous
        monogamous = not any(
            'non monogamous' in (record.get('Select all that you feel is true ', '') or '').lower()
            for record in records
        )
        
        return jsonify({
            'status': status_data,
            'last_entries': last_entries_data,
            'memories_and_worries': memories_and_worries,
            '30_day_trends': trend_data,
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
        response = send_weekly_email()
        if response:
            return response
        else:
            return jsonify({"error": "Failed to send email"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test-email')
def test_simple_email():
    """Send a simple test email"""
    try:
        print(f"Using API key: {RESEND_API_KEY[:10] if RESEND_API_KEY else 'None'}...")
        print(f"From email: {EMAIL_FROM}")
        print(f"To emails: {EMAIL_TO}")
        
        if not RESEND_API_KEY:
            return jsonify({"error": "RESEND_API_KEY not set"}), 500
        
        email_to_list = [email.strip() for email in EMAIL_TO.split(',')]
        print(f"Sending email to: {email_to_list}")
        
        try:
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
            
        except resend.exceptions.ResendError as e:
            print(f"Resend API Error: {e}")
            print(f"Error details: {getattr(e, 'message', 'No message')}")
            print(f"Error code: {getattr(e, 'code', 'No code')}")
            return jsonify({
                "error": f"Resend API Error: {e}",
                "details": getattr(e, 'message', 'No message'),
                "code": getattr(e, 'code', 'No code')
            }), 500
        
    except Exception as e:
        print(f"General error: {e}")
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
            gift_message = os.getenv('GIFT_MESSAGE', 'Error loading the awesome gift message I wrote.')
            gift_data = {
                "unlocked": True,
                "message": "correct password.",
                "gift_content": {
                    "title": "happy 5 months!!!! ",
                    "subtitle": "",
                    "sections": [
                        {
                            "type": "message",
                            "content": gift_message
                        },
                        {
                            "type": "preview_images",
                            "title": "",
                            "images": [
                                {
                                    "src": "gift-assets/michael-preview.png",
                                    "alt": "Michael Preview"
                                },
                                {
                                    "src": "gift-assets/amy-preview.png", 
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
                                    "file": "gift-assets/michael_classic.png",
                                    "filename": "michael_classic.png"
                                },
                                {
                                    "name": "Download Slim",
                                    "file": "gift-assets/michael_slim.png",
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