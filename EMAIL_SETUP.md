# Weekly Email Setup Instructions

## 1. Set Up Resend Account
1. Go to [resend.com](https://resend.com)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Verify your domain (or use their test domain)

## 2. Configure Environment Variables
Add these to your deployment platform (Vercel/Railway/etc.):

```
RESEND_API_KEY=re_your_api_key_here
EMAIL_FROM=noreply@yourdomain.com
EMAIL_TO=amy@example.com,michael@example.com
```

## 3. Deploy Your App
Make sure your app is deployed and the `/send-email` endpoint works.

## 4. Test the Email
Visit: `https://your-app-url.com/send-email` to manually trigger an email.

## 5. GitHub Actions Setup
The workflow will automatically run every Sunday at 9 AM UTC.

### Manual Trigger
You can also manually trigger the email from GitHub:
1. Go to your repository
2. Click "Actions"
3. Select "Weekly Relationship Email"
4. Click "Run workflow"

## 6. Customize Email Content
Edit the `generate_weekly_email()` function in `app.py` to customize:
- Email template design
- Content sections
- Styling
- Subject line

## 7. Troubleshooting
- Check GitHub Actions logs for errors
- Verify your Resend API key is correct
- Ensure email addresses are valid
- Test manually first before relying on automation

## Email Schedule
- **Automatic**: Every Sunday at 9 AM UTC
- **Manual**: Any time via GitHub Actions or API endpoint 