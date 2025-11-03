# Driver GTM - Final Working Version

## Overview

Driver GTM is a comprehensive freight logistics system that helps identify the best loads for available drivers using KAYAAN Profit Score. The system integrates with DAT (Digital Asset Trading) API to search for drivers and loads, filters drivers by company size (≤10 trucks), and ranks loads based on profit potential, market connectivity, and ease of booking.

## System Architecture

### Backend (Flask API)
- **Port**: 5004
- **Framework**: Flask with CORS enabled
- **Main Files**:
  - `app.py` - Main Flask application with API endpoints
  - `dat_client.py` - DAT API client with authentication
  - `efrouting.py` - KAYAAN Profit Score calculation engine
  - `num_trucks.py` - USDOT API integration for company truck/driver data
  - `city_database.py` - City coordinates database

### Frontend
- **File**: `index.html` - Single-page application
- **Features**: Driver search, load ranking, driver details, email generation

## Key Features

### 1. Driver Search & Filtering
- Search drivers by location (state/city), equipment type
- **Automatic filtering**: Only shows drivers from companies with ≤10 trucks
- USDOT API integration to verify company truck counts
- Display of truck count and total drivers on driver cards
- Shows all filtered drivers (up to 150 from DAT API, then filtered)

### 2. Load Ranking with KAYAAN Profit Score
- **Profit Component (50% weight)**:
  - Revenue per mile
  - Profit per mile
  - Total revenue
  - Trip distance consideration
  
- **Connectivity Component (30% weight)**:
  - Market connectivity score
  - Lane connectivity analysis
  
- **Ease of Booking (20% weight)**:
  - Market conditions
  - Supply/demand ratios
  - Outbound load availability

### 3. USDOT Integration
- Fetches company data from USDOT API using DOT numbers
- Displays: Number of trucks, total drivers, legal name, MC number, physical address
- Used for filtering (companies with ≤10 trucks only)
- Caches API responses to reduce redundant calls

### 4. Environment Support
- **Staging**: Test environment (default)
- **Production**: Live environment with UI credential input
- Automatic authentication handling and token refresh

### 5. Load Filtering
- Filter by driver availability window
- Filter by load type (FULL, PARTIAL, BOTH)
- Filter by maximum deadhead distance

## Installation

### Prerequisites
- Python 3.11+
- pip
- DAT API credentials

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file with DAT credentials:
```env
DAT_USERNAME=your_dat_username@company.com
DAT_PASSWORD=your_dat_password
DAT_USER=your_dat_user@company.com
```

4. Run the server:
```bash
python app.py
```

Server will start on `http://localhost:5004`

### Frontend Setup

No build required - the Flask app serves the frontend at `http://localhost:5004` or open `frontend/index.html` directly in a browser.

## API Endpoints

### POST `/api/search-drivers`
Search for available drivers/capacity.

**Request Body**:
```json
{
  "origin_state": "TX",
  "origin_city": "Houston" (optional),
  "equipment_types": ["V"],
  "filters": {
    "max_deadhead": 50
  },
  "limit": 150,
  "environment": "staging",
  "production_credentials": null (or {username, password, user} for production)
}
```

**Response**:
```json
{
  "drivers": [
    {
      "company_name": "Company Name",
      "credentials": {
        "dot_number": 1234567,
        "mc_number": 987654
      },
      "usdot_data": {
        "truck_units": 5,
        "total_drivers": 8,
        "legal_name": "Legal Company Name",
        "phy_city": "City",
        "phy_state": "ST"
      },
      "location": {
        "city": "Houston",
        "state": "TX"
      },
      "capacity": {
        "length_feet": 53,
        "weight_pounds": 45000
      },
      "service_flags": {
        "is_bookable": true,
        "is_negotiable": false,
        "is_factorable": true,
        "is_trackable": true
      }
    }
  ],
  "total_count": 168,
  "returned_count": 10
}
```

### POST `/api/get-loads-for-driver`
Get ranked loads for a selected driver using KAYAAN Profit Score.

**Request Body**:
```json
{
  "driver_location_city": "Houston",
  "driver_location_state": "TX",
  "equipment_type": "V",
  "driver_availability": {
    "earliestWhen": "2025-10-31T15:00:00Z",
    "latestWhen": "2025-11-01T06:59:59.999Z"
  },
  "load_type": "BOTH",
  "environment": "staging",
  "production_credentials": null
}
```

**Response**:
```json
{
  "loads": [
    {
      "match_id": "load_id",
      "origin": {
        "city": "Houston",
        "state": "TX"
      },
      "destination": {
        "city": "Dallas",
        "state": "TX"
      },
      "composite_data": {
        "composite_score": 85,
        "recommendation": "Excellent"
      },
      "profit_data": {
        "rate_per_mile": 2.50,
        "profit_per_mile": 1.10,
        "total_revenue": 1250
      },
      "broker_info": {
        "company_name": "Broker Name",
        "dot_number": 1234567,
        "usdot_data": {
          "truck_units": 12,
          "total_drivers": 18
        }
      },
      "load_details": {
        "weight_pounds": 45000,
        "length_feet": 53,
        "full_partial": "FULL",
        "commodity": "General Freight",
        "reference_id": "REF123"
      }
    }
  ],
  "total_count": 50,
  "analyzed_with": "KAYAAN Profit Score"
}
```

### GET `/api/states`
Get list of all US states.

### GET `/api/cities/<state>`
Get cities for a specific state.

### GET `/health`
Health check endpoint.

## Filtering Logic

### Driver Filtering (≤10 Trucks)
1. For each driver, extract DOT number from DAT API
2. Query USDOT API to get company truck count
3. If truck count ≤ 10: Include driver
4. If truck count > 10: Exclude driver
5. If DOT missing or API fails: Include driver (can't verify)

**Note**: The system searches up to 150 drivers from DAT API, then filters them to only show companies with ≤10 trucks. This ensures you see ALL matching small carriers, not just the first 10.

### Load Filtering
- **By Driver Availability**: Only shows loads where pickup window is within driver's availability window
- **By Load Type**: Filter by FULL, PARTIAL, or BOTH
- **By Deadhead**: Configurable maximum deadhead miles

## Scoring Algorithm (KAYAAN Profit Score)

The composite score combines three components:

1. **Profit Score (50% weight)**: Based on revenue per mile, profit per mile, and total revenue
2. **Connectivity Score (30% weight)**: Based on market connectivity and lane availability
3. **Ease Score (20% weight)**: Based on market conditions and booking ease

Final score: `0-100` where higher is better.

### Score Recommendations
- **90-100**: Excellent - Highly profitable with great connectivity
- **75-89**: Good - Strong profit potential
- **60-74**: Moderate - Decent opportunity
- **Below 60**: Low - Consider alternatives

## Data Display

### Driver Cards Show:
- Company name, equipment type
- DOT and MC numbers (as badges)
- Location, availability, destination
- Phone, email
- Truck capacity (length × weight)
- **🚚 Number of Trucks** (from USDOT, always visible)
- **👥 Total Drivers** (from USDOT, always visible)
- Service flags (Bookable, Negotiable, Factorable, Trackable)

### Driver Details Show:
- All card information plus:
- Carrier home state
- Availability end date
- Preferred contact method
- Posting ID and expiration
- Driver comments
- Full USDOT registry information section (green highlight):
  - Legal Name
  - Number of Trucks (prominently displayed)
  - Total Drivers (prominently displayed)
  - USDOT MC Number
  - Physical City/State
  - Entity Type

### Load Cards Show:
- Route (origin → destination)
- KAYAAN Profit Score with color coding
- Pickup window (formatted, readable)
- Load details section:
  - Weight, length, load type
  - Commodity, reference ID, equipment type
  - Special instructions, comments
- Broker information with **🚚 Number of Trucks** and **👥 Total Drivers**
- Market analysis
- Profit metrics
- Email generation capability (copy-ready template)

## Configuration

### USDOT API
- **Base URL**: `https://data.transportation.gov/resource/az4n-8mr2.json`
- **App Token**: Set via `USDOT_APP_TOKEN` environment variable (required)
- **Secret Token**: Set via `USDOT_SECRET_TOKEN` environment variable (optional)
- **Caching**: In-memory cache to reduce API calls
- **Timeout**: 5 seconds per request

### DAT API Limits
- **Maximum safe limit**: 150 drivers per search
- Higher limits (200+) may cause API failures or timeouts
- Default limit in code: 150

### Authentication
- **Token lifetime**: 15 minutes (auto-refreshes)
- **Caching**: Tokens cached until expiration
- **Environments**: Separate credentials for staging and production

## Troubleshooting

### "Failed to search drivers"
**Possible causes**:
- DAT API authentication failed - check credentials
- DAT API limit too high - reduce to 150 or less
- Network/timeout issues - check backend logs
- Invalid search parameters - verify origin state is valid

**Solution**: Check backend terminal logs for specific error messages. The logs will show:
- Authentication status
- DAT API response codes
- Specific error details

### "Number of Trucks: N/A"
**Possible causes**:
- USDOT API doesn't have data for that DOT number
- DOT number is missing or invalid
- USDOT API timeout or error

**Solution**: Check backend logs for USDOT API errors. The system includes drivers even if USDOT data is unavailable (benefit of the doubt).

### Authentication Errors
**For Staging**:
- Ensure DAT credentials are correct in `.env` file
- Check that credentials are valid for staging environment

**For Production**:
- Use UI credential input fields when selecting "Production"
- Fill in all three fields: username, password, user email
- Ensure credentials are valid for production environment

### Frontend Shows "N/A" for Truck Counts
- This is expected if USDOT API doesn't have data
- Fields are always visible (shows "N/A" in gray when unavailable)
- Check backend logs to see if API calls are being made

## File Structure

```
Driver_GTM_auto/
├── backend/
│   ├── app.py              # Main Flask application (754 lines)
│   ├── dat_client.py       # DAT API client (410 lines)
│   ├── efrouting.py        # KAYAAN Profit Score algorithm (485 lines)
│   ├── num_trucks.py       # USDOT API integration (141 lines)
│   ├── city_database.py    # City coordinates database (434 lines)
│   ├── requirements.txt    # Python dependencies
│   └── __pycache__/       # Python cache (excluded from git)
├── frontend/
│   └── index.html          # Single-page frontend (1834 lines)
└── README.md              # This file
```

## Dependencies

### Backend (`requirements.txt`)
```
flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
python-dotenv==1.0.0
```

## Usage Workflow

1. **Start Backend**:
   ```bash
   cd backend
   python app.py
   ```

2. **Open Frontend**:
   - Navigate to `http://localhost:5004` in browser
   - Or open `frontend/index.html` directly

3. **Search for Drivers**:
   - Select state (required)
   - Optionally select city
   - Choose equipment type
   - Set maximum deadhead distance
   - Select environment (Staging/Production)
   - If Production: Enter credentials in UI
   - Click "Search Drivers"

4. **Select a Driver**:
   - Click on any driver card to see details
   - View USDOT data, capacity, service flags
   - System automatically searches for loads

5. **Review Load Rankings**:
   - Loads are ranked by KAYAAN Profit Score
   - Higher scores = better opportunities
   - Click "Generate Driver Email" to create email template
   - Click "View Raw Data" to see full API response

6. **Filter Loads** (Optional):
   - Use "Load Type" dropdown: Full, Partial, or Both
   - System automatically filters by driver availability

## Key Implementation Details

### Authentication Flow
1. Get organization token using username/password
2. Get user token using organization token + user email
3. Tokens cached for 15 minutes
4. Auto-refreshes when expired

### USDOT Data Fetching
1. Extract DOT number from driver data
2. Check in-memory cache first
3. If not cached, query USDOT API
4. Parse response (handles string values from API)
5. Cache result for future use

### Driver Filtering Process
1. Fetch up to 150 drivers from DAT API
2. For each driver, check USDOT API for truck count
3. If truck count ≤ 10: Keep driver
4. If truck count > 10: Exclude driver
5. If can't verify: Keep driver (benefit of doubt)
6. Return all filtered drivers to frontend

### Load Ranking Process
1. Fetch loads from DAT API based on driver location
2. Filter by driver availability window
3. Filter by load type if specified
4. Calculate profit scores
5. Fetch market data for destination
6. Calculate composite KAYAAN Profit Score
7. Sort by score (highest first)

## Performance Considerations

- **USDOT API Caching**: Reduces redundant API calls for same DOT numbers
- **DAT Token Caching**: Tokens cached to avoid frequent re-authentication
- **Request Timeout**: Frontend has 120-second timeout for API calls
- **Limit Optimization**: Uses 150 limit (safe for DAT API) instead of higher values

## Security Notes

- DAT credentials stored in `.env` file (not in code)
- Production credentials can be entered in UI (not persisted)
- CORS enabled for local development
- No sensitive data logged to console

## Version Information

- **Version**: Final Working Version
- **Last Updated**: November 2025
- **DAT API**: v3
- **Python**: 3.11+
- **Flask**: 3.0.0
- **Frontend**: Vanilla JavaScript (no frameworks)

## Recent Improvements

- ✅ Fixed USDOT data parsing (handles string values from API)
- ✅ Improved error handling and logging
- ✅ Optimized authentication to avoid redundant calls
- ✅ Added prominent display of truck/driver counts
- ✅ Fixed DAT API limit issues (reduced to 150)
- ✅ Enhanced filtering logic (shows all drivers ≤10 trucks)
- ✅ Added broker truck/driver count to load cards
- ✅ Improved timeout handling

## Notes

- Driver searches are automatically saved to `saved_data/` folder (in original project)
- USDOT API responses are cached in-memory (per server instance)
- Authentication tokens are cached and auto-refreshed
- Frontend has 120-second timeout for API calls
- All drivers shown are from companies with ≤10 trucks (when verifiable)
- Fields always visible (shows "N/A" when data unavailable)

## Support & Debugging

### Backend Logs
Check terminal where `app.py` is running for:
- 🔍 Search operations
- ✅ Successful operations
- ⚠️  Warnings (missing data, API failures)
- ❌ Errors (with full tracebacks)

### Frontend Debugging
- Open browser console (F12)
- Check Network tab for API requests
- Look for error messages in console

### Common Log Messages
- `🚛 Filtering drivers: Only showing companies with <= 10 trucks`
- `✅ Including: Company Name (DOT: 12345, Trucks: 5)`
- `❌ Excluding: Company Name (DOT: 67890, Trucks: 15 > 10)`
- `📊 USDOT data fetched for DOT 12345: 5 trucks`

## License

Internal use only.

