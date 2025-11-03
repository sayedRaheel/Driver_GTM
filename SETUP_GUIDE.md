# Quick Setup Guide

## Step 1: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 2: Configure DAT Credentials

Create a `.env` file in the `backend/` directory:

```bash
cd backend
touch .env
```

Add your credentials to `.env`:
```
# DAT API Credentials (Required)
DAT_USERNAME=your_dat_username@company.com
DAT_PASSWORD=your_dat_password
DAT_USER=your_dat_user@company.com

# USDOT API Credentials (Required)
USDOT_APP_TOKEN=your_usdot_app_token
USDOT_SECRET_TOKEN=your_usdot_secret_token
```

## Step 3: Start the Server

```bash
python app.py
```

You should see:
```
🚀 Driver GTM API Server
   Port: 5004
```

## Step 4: Open the Frontend

Open your browser and navigate to:
```
http://localhost:5004
```

Or directly open:
```
frontend/index.html
```

## Step 5: Start Searching

1. Select a state (required)
2. Optionally select a city
3. Choose equipment type (Van, Reefer, Flatbed)
4. Set max deadhead distance
5. Click "Search Drivers"

## Production Mode

To use Production environment:
1. Select "Production" from the Environment dropdown
2. Enter your production credentials in the form that appears
3. Fill in: Username, Password, User Email
4. Search as normal

## Troubleshooting

**Server won't start?**
- Check Python version: `python --version` (should be 3.11+)
- Install dependencies: `pip install -r requirements.txt`
- Check if port 5004 is available

**"Failed to authenticate" error?**
- Verify DAT credentials in `.env` file
- Check that credentials are correct for selected environment
- For production, use UI credential input fields

**No drivers showing?**
- Check backend terminal logs
- Verify search parameters (state is required)
- Try different states or equipment types

**USDOT data showing "N/A"?**
- This is normal for some companies
- Check backend logs for USDOT API errors
- System includes drivers even if USDOT data unavailable

## Need Help?

Check the main `README.md` for detailed documentation.

