
 love
Creating a dashboard for me and my lover. At michaelamy5ever.com 

## 🌟 Features

- **Real-time Dashboard**: Displays relationship status, memories, and worries
- **Google Sheets Integration**: Fetches data from public Google Sheets
- **Weekly Email Updates**: Automated relationship summaries via Resend
- **Face Matching**: Simple face embedding comparison (experimental)
- **Responsive Design**: Works on desktop and mobile

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Sheets with public sharing enabled
- Resend account (for email features)

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd love
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the root directory:
```env
# Google Sheets
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit

# Email Service (Resend)
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM=onboarding@resend.dev
EMAIL_TO=your-email@example.com

```

### 5. Run Locally
```bash
python app.py
```
The API will be available at `http://localhost:5001`

### 6. Open Dashboard
Open `index.html` in your browser or serve it with a local server:
```bash
python -m http.server 8000
```
Then visit `http://localhost:8000`

## 📁 Project Structure

```
love/
├── app.py                 # Flask backend API
├── index.html            # Main dashboard
├── face-embedding-simple.html  # Face matching page
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
└── README.md
```

## 🔧 Configuration

### Google Sheets Setup
1. Create a Google Sheet with your relationship data
2. Make it publicly accessible (Anyone with the link can view)
3. Copy the URL and add it to `GOOGLE_SHEET_URL` in your `.env`

### Email Setup (Optional)
1. Sign up for [Resend](https://resend.com)
2. Get your API key
3. Add it to `RESEND_API_KEY` in your `.env`
4. Set your email addresses in `EMAIL_FROM` and `EMAIL_TO`

## 🌐 Deployment

### Backend (Vercel)
1. Connect your GitHub repo to Vercel
2. Add environment variables in Vercel dashboard
3. Deploy automatically on push

### Frontend (GitHub Pages)
1. Push your code to GitHub
2. Enable GitHub Pages in repository settings
3. Set source to main branch

## 📊 API Endpoints

- `GET /` - API info and available endpoints
- `GET /hangout-data` - Main dashboard data
- `GET /status` - Status summary only
- `GET /last-entries` - Latest entries for each user
- `POST /face-match` - Face matching endpoint
- `GET /send-email` - Trigger weekly email manually
- `GET /test` - Health check

## 📧 Email Features (WORK IN PROGRESS)

- Weekly automated relationship summaries
- Manual trigger endpoint for testing
- HTML email templates with relationship data
- Configurable recipients and sender

## 🛠️ Development

### Local Development
1. Set `API_URL` to `http://localhost:5001/hangout-data` in `index.html`
2. Run Flask backend: `python app.py`
3. Open `index.html` in browser

### Production
1. Set `API_URL` to your deployed backend URL
2. Deploy backend to Vercel
3. Deploy frontend to GitHub Pages

### Debugging
- Check Flask console for backend logs
- Use browser DevTools for frontend debugging
- Test API endpoints directly in browser

## 🔒 Security Notes

- Google Sheets should be public for this setup
- Consider rate limiting for production use
- Email API keys should be kept secure

## 📝 License

Private project for Amy and Michael 💕

---

**Need help?** Check the Flask console logs and browser DevTools for debugging information.
