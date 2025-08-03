#!/usr/bin/env python3
"""
Debug script to test email configuration
"""

import os
from dotenv import load_dotenv
import resend

# Load environment variables
load_dotenv()

# Get configuration
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'onboarding@resend.dev')
EMAIL_TO = os.getenv('EMAIL_TO', 'fineshyts@michaelamy5ever.com')

print("=== Email Configuration Debug ===")
print(f"RESEND_API_KEY: {'Set' if RESEND_API_KEY else 'NOT SET'}")
if RESEND_API_KEY:
    print(f"API Key (first 10 chars): {RESEND_API_KEY[:10]}...")
print(f"EMAIL_FROM: {EMAIL_FROM}")
print(f"EMAIL_TO: {EMAIL_TO}")

# Test basic Resend setup
if RESEND_API_KEY:
    try:
        resend.api_key = RESEND_API_KEY
        print("\n✅ Resend API key set successfully")
        
        # Test with different sender emails
        test_senders = [
            "onboarding@resend.dev",
            "noreply@michaelamy5ever.com", 
            "hello@michaelamy5ever.com",
            "amy@michaelamy5ever.com",
            "michael@michaelamy5ever.com"
        ]
        
        email_to_list = [email.strip() for email in EMAIL_TO.split(',')]
        
        for sender in test_senders:
            print(f"\n🔍 Testing sender: {sender}")
            try:
                response = resend.Emails.send({
                    "from": sender,
                    "to": email_to_list,
                    "subject": f"🔧 Email Test - {sender}",
                    "html": f"<h1>Email Test</h1><p>Testing sender: {sender}</p>"
                })
                print(f"✅ SUCCESS with {sender}! ID: {response['id']}")
                print(f"🎉 Use this sender email: {sender}")
                break
                
            except resend.exceptions.ResendError as e:
                print(f"❌ Failed with {sender}: {e}")
                if hasattr(e, 'code'):
                    print(f"   Error code: {e.code}")
                if hasattr(e, 'message'):
                    print(f"   Error message: {e.message}")
                    
    except Exception as e:
        print(f"\n❌ General error: {e}")
else:
    print("\n❌ RESEND_API_KEY not set in environment variables")
    print("Please set RESEND_API_KEY in your .env file")

print("\n📋 Next steps:")
print("1. If no sender works, verify your domain in Resend dashboard")
print("2. Or use a verified email address")
print("3. Update EMAIL_FROM in your .env file with the working sender") 