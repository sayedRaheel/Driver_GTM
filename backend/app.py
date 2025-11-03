#!/usr/bin/env python3
"""
Driver GTM - Flask API Server
Port 5004
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from dat_client import DATClient
from efrouting import analyze_loads_for_driver
from city_database import get_cities_by_state, get_city_coordinates
from num_trucks import get_truck_count, get_usdot_data

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize DAT clients (one for each environment)
dat_clients = {
    'staging': None,
    'production': None
}

def get_dat_client(environment='staging'):
    """Get or create authenticated DAT client for specified environment"""
    global dat_clients

    if environment not in ['staging', 'production']:
        environment = 'staging'

    if dat_clients[environment] is None:
        username = os.getenv("DAT_USERNAME")
        password = os.getenv("DAT_PASSWORD")
        user = os.getenv("DAT_USER")

        if not all([username, password, user]):
            raise ValueError("Missing DAT credentials in environment variables")

        dat_clients[environment] = DATClient(username, password, user, environment=environment)

    # Always authenticate to ensure we have valid token
    if not dat_clients[environment].authenticate():
        # Try to reset and authenticate again
        dat_clients[environment] = None
        dat_clients[environment] = DATClient(os.getenv("DAT_USERNAME"), os.getenv("DAT_PASSWORD"), os.getenv("DAT_USER"), environment=environment)
        if not dat_clients[environment].authenticate():
            raise Exception(f"Failed to authenticate with DAT {environment}")

    return dat_clients[environment]


def filter_drivers_by_truck_count(drivers: list, max_trucks: int = 10) -> list:
    """
    Filter drivers to only include companies with <= max_trucks trucks
    
    Args:
        drivers: List of driver data from DAT API (raw format, before formatting)
        max_trucks: Maximum number of trucks allowed (default: 10)
        
    Returns:
        Filtered list of drivers
    """
    if not drivers:
        return drivers
    
    filtered_drivers = []
    companies_checked = {}  # Cache truck counts by DOT number within this filter call
    
    print(f"🚛 Filtering drivers: Only showing companies with <= {max_trucks} trucks")
    
    for driver in drivers:
        # Extract DOT number
        poster_dot_ids = driver.get("posterDotIds", {})
        dot_number = poster_dot_ids.get("dotNumber")
        
        if not dot_number or dot_number == "N/A" or dot_number == 0:
            # If no DOT number, include them (can't verify, so give benefit of doubt)
            company_name = driver.get("posterInfo", {}).get("companyName", "Unknown")
            print(f"⚠️  Driver with no DOT number, including: {company_name}")
            filtered_drivers.append(driver)
            continue
        
        # Check if we already checked this DOT number in this filtering pass
        dot_str = str(dot_number)
        if dot_str in companies_checked:
            truck_count = companies_checked[dot_str]
        else:
            # Call USDOT API to get truck count
            try:
                truck_count = get_truck_count(dot_str)
            except Exception as e:
                print(f"⚠️  Error getting truck count for DOT {dot_str}: {str(e)}")
                truck_count = None  # If API fails, include driver (can't verify)
            companies_checked[dot_str] = truck_count
        
        # Filter logic: Include if truck_count is None (API failed) or <= max_trucks
        company_name = driver.get("posterInfo", {}).get("companyName", "Unknown")
        
        if truck_count is None:
            # API call failed or no data - include driver (can't verify, so include)
            print(f"⚠️  Could not verify truck count for DOT {dot_number} ({company_name}), including driver")
            filtered_drivers.append(driver)
        elif truck_count <= max_trucks:
            # Company has acceptable number of trucks
            print(f"✅ Including: {company_name} (DOT: {dot_number}, Trucks: {truck_count})")
            filtered_drivers.append(driver)
        else:
            # Company has too many trucks - exclude
            print(f"❌ Excluding: {company_name} (DOT: {dot_number}, Trucks: {truck_count} > {max_trucks})")
    
    print(f"📊 Filtered {len(filtered_drivers)}/{len(drivers)} drivers (companies with <= {max_trucks} trucks)")
    return filtered_drivers


def save_driver_data_to_json(drivers: list, search_params: dict, total_count: int):
    """
    Save driver search results to JSON file with datetime and lane information

    Args:
        drivers: List of formatted driver data
        search_params: Search parameters used (origin, equipment, filters, etc.)
        total_count: Total number of drivers found
    """
    try:
        # Create saved_data directory if it doesn't exist
        save_dir = os.path.join(os.path.dirname(__file__), '..', 'saved_data')
        os.makedirs(save_dir, exist_ok=True)

        # Generate filename with datetime and lane info
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        origin_city = search_params.get('origin_city', 'Unknown')
        origin_state = search_params.get('origin_state', 'XX')

        # Create lane label (origin city-state)
        lane_label = f"{origin_city}_{origin_state}" if origin_city else origin_state
        filename = f"drivers_{lane_label}_{timestamp}.json"
        filepath = os.path.join(save_dir, filename)

        # Prepare data to save
        save_data = {
            "search_metadata": {
                "timestamp": now.isoformat(),
                "search_date": now.strftime("%Y-%m-%d"),
                "search_time": now.strftime("%H:%M:%S"),
                "lane": {
                    "origin_city": origin_city,
                    "origin_state": origin_state,
                    "label": lane_label
                },
                "search_parameters": search_params,
                "total_drivers_found": total_count,
                "drivers_returned": len(drivers)
            },
            "drivers": drivers
        }

        # Write to JSON file
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)

        print(f"✅ Saved {len(drivers)} drivers to {filename}")

    except Exception as e:
        print(f"❌ Error saving driver data to JSON: {str(e)}")
        # Don't raise exception - saving is non-critical


@app.route('/api/search-drivers', methods=['POST'])
def search_drivers():
    """
    Search for drivers/capacity

    Request body:
    {
        "origin_city": "Houston" (optional),
        "origin_state": "TX",
        "equipment_types": ["V", "R"],
        "filters": {
            "availability_start": "2025-01-15T00:00:00Z" (optional),
            "availability_end": "2025-01-20T00:00:00Z" (optional),
            "destination_state": "CA" (optional),
            "max_deadhead": 50 (optional)
        },
        "limit": 10,
        "environment": "staging" or "production" (optional, defaults to staging)
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        origin_city = data.get('origin_city')
        origin_state = data.get('origin_state')
        equipment_types = data.get('equipment_types', ['V'])
        filters = data.get('filters', {})
        limit = data.get('limit', 150)  # Safe limit for DAT API (max ~200), then filter by truck count (≤10 trucks)
        environment = data.get('environment', 'staging')
        production_credentials = data.get('production_credentials')

        if not origin_state:
            return jsonify({"error": "origin_state is required"}), 400

        # Get DAT client with specified environment and credentials
        try:
            if environment == 'production':
                if production_credentials:
                    # Use production credentials from frontend
                    username = production_credentials.get('username')
                    password = production_credentials.get('password')
                    user = production_credentials.get('user')
                    
                    if not all([username, password, user]):
                        return jsonify({'error': 'Production credentials are required for production environment'}), 400
                    
                    # Create client with production credentials
                    client = DATClient(username=username, password=password, user=user, environment='production')
                    if not client.authenticate():
                        return jsonify({'error': 'Failed to authenticate with DAT production using provided credentials'}), 401
                else:
                    # Production selected but no credentials provided
                    return jsonify({'error': 'Production credentials are required when using Production environment. Please fill in all credential fields in the UI.'}), 400
            else:
                # Use default client (staging)
                client = get_dat_client(environment)
        except ValueError as e:
            print(f"❌ Configuration error: {str(e)}")
            return jsonify({"error": f"Configuration error: {str(e)}. Please check your DAT credentials."}), 500
        except Exception as e:
            print(f"❌ Failed to get DAT client: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Failed to initialize DAT client: {str(e)}"}), 500

        # Search for drivers (client is already authenticated by get_dat_client)
        print(f"🔍 Searching drivers: state={origin_state}, city={origin_city}, equipment={equipment_types}, limit={limit}")
        try:
            drivers, total_count = client.search_drivers(
                origin_city=origin_city,
                origin_state=origin_state,
                equipment_types=equipment_types,
                filters=filters,
                limit=limit
            )
        except Exception as e:
            print(f"❌ Exception in client.search_drivers: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Error searching drivers: {str(e)}"}), 500

        if drivers is None:
            print(f"❌ client.search_drivers returned None")
            print(f"   Check the logs above for specific DAT API errors")
            # Safely check client state
            try:
                client_authenticated = client.access_token is not None if client else False
                api_calls = client.api_calls if client else 0
                print(f"   Client state - authenticated: {client_authenticated}, API calls: {api_calls}")
            except Exception as e:
                print(f"   Could not check client state: {str(e)}")
            
            # Check if it's an authentication issue or API issue
            error_msg = "Failed to search drivers. "
            try:
                if client and not client.access_token:
                    error_msg += "Authentication failed. "
            except:
                pass
            error_msg += "Check backend terminal logs for detailed error messages or try again."
            return jsonify({"error": error_msg}), 500

        # Filter drivers by truck count (only companies with <= 10 trucks)
        if drivers and len(drivers) > 0:
            original_count = len(drivers)
            drivers = filter_drivers_by_truck_count(drivers, max_trucks=10)
            print(f"🚛 After truck count filtering: {len(drivers)}/{original_count} drivers remain")
        elif drivers is not None and len(drivers) == 0:
            print(f"⚠️  No drivers found from DAT API (may be filtered out)")
            drivers = []  # Ensure it's an empty list, not None

        # Format driver data for frontend
        formatted_drivers = []
        for driver in drivers:
            asset_info = driver.get("matchingAssetInfo", {})
            origin = asset_info.get("origin", {})
            destination = asset_info.get("destination", {})
            poster = driver.get("posterInfo", {})
            contact = poster.get("contact", {})
            availability = driver.get("availability", {})

            # Extract DOT and MC numbers
            poster_dot_ids = driver.get("posterDotIds", {})
            dot_number = poster_dot_ids.get("dotNumber", "N/A")
            mc_number = poster_dot_ids.get("carrierMcNumber", "N/A")
            
            # Get USDOT API data
            usdot_data = None
            if dot_number and dot_number != "N/A" and dot_number != 0:
                try:
                    print(f"🔍 Fetching USDOT data for DOT {dot_number} (Company: {poster.get('companyName', 'Unknown')})")
                    usdot_data = get_usdot_data(str(dot_number))
                    if usdot_data:
                        print(f"✅ USDOT data retrieved: {usdot_data.get('truck_units', 'N/A')} trucks, {usdot_data.get('total_drivers', 'N/A')} drivers")
                    else:
                        print(f"⚠️  No USDOT data found for DOT {dot_number}")
                except Exception as e:
                    print(f"⚠️  Error fetching USDOT data for driver DOT {dot_number}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    usdot_data = None  # Continue without USDOT data
            else:
                company_name = poster.get("companyName", "Unknown")
                print(f"⚠️  Skipping USDOT lookup - DOT number is missing/invalid: {dot_number} (Company: {company_name})")
            
            # Extract truck capacity information
            available_length = driver.get("availableLengthFeet", "N/A")
            available_weight = driver.get("availableWeightPounds", "N/A")
            
            # Extract service flags
            service_flags = {
                "is_bookable": driver.get("isBookable", False),
                "is_negotiable": driver.get("isNegotiable", False),
                "is_factorable": driver.get("isFactorable", False),
                "is_assurable": driver.get("isAssurable", False),
                "is_trackable": driver.get("isTrackable", False)
            }

            formatted_driver = {
                "match_id": driver.get("matchId", ""),
                "company_name": poster.get("companyName", "N/A"),
                "equipment_type": asset_info.get("equipmentType", "N/A"),
                "location": {
                    "city": origin.get("city", "N/A"),
                    "state": origin.get("stateProv", "N/A")
                },
                "availability": {
                    "earliest": availability.get("earliestWhen", "N/A"),
                    "latest": availability.get("latestWhen", "N/A")
                },
                "destination": {
                    "city": destination.get("place", {}).get("city", "Open"),
                    "state": destination.get("place", {}).get("stateProv", "Open")
                },
                "contact": {
                    "phone": contact.get("phoneNumber") or contact.get("phone") or "N/A",
                    "email": contact.get("email", "N/A")
                },
                "deadhead": driver.get("originDeadheadMiles", {}).get("miles", 0),
                "credentials": {
                    "dot_number": dot_number,
                    "mc_number": mc_number
                },
                "usdot_data": usdot_data,  # Full USDOT API data
                "capacity": {
                    "length_feet": available_length,
                    "weight_pounds": available_weight
                },
                "service_flags": service_flags,
                "comments": driver.get("comments", "N/A"),  # Driver comments
                "posting_id": driver.get("postingId", "N/A"),  # Posting ID
                "posting_expires": driver.get("postingExpiresWhen", "N/A"),  # Posting expiration
                "carrier_home_state": poster.get("carrierHomeState", "N/A"),  # Carrier home state
                "preferred_contact_method": poster.get("preferredContactMethod", "N/A"),  # Preferred contact method
                "raw_data": driver  # Include full data for detail view
            }

            formatted_drivers.append(formatted_driver)

        # Save driver data to JSON file with datetime and lane information
        save_driver_data_to_json(
            drivers=formatted_drivers,
            search_params={
                "origin_city": origin_city,
                "origin_state": origin_state,
                "equipment_types": equipment_types,
                "filters": filters,
                "environment": environment
            },
            total_count=total_count
        )

        return jsonify({
            "drivers": formatted_drivers,
            "total_count": total_count,
            "returned_count": len(formatted_drivers)
        })

    except Exception as e:
        print(f"Error in search_drivers: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def filter_loads_by_type(loads, load_type_filter):
    """
    Filter loads based on load type (FULL, PARTIAL, BOTH)
    
    Args:
        loads: List of load data from DAT API
        load_type_filter: Filter type ('FULL', 'PARTIAL', 'BOTH')
    
    Returns:
        Filtered list of loads
    """
    if not load_type_filter or not loads:
        return loads
    
    filtered_loads = []
    
    for load in loads:
        asset_info = load.get("matchingAssetInfo", {})
        load_full_partial = asset_info.get("capacity", {}).get("shipment", {}).get("fullPartial", "")
        
        # Check if load matches the filter
        if load_type_filter == "BOTH":
            # Include both FULL and PARTIAL loads
            if load_full_partial in ["FULL", "PARTIAL"]:
                filtered_loads.append(load)
        elif load_type_filter == load_full_partial:
            # Exact match
            filtered_loads.append(load)
        elif load_type_filter == "FULL" and load_full_partial == "FULL":
            filtered_loads.append(load)
        elif load_type_filter == "PARTIAL" and load_full_partial == "PARTIAL":
            filtered_loads.append(load)
    
    return filtered_loads


def filter_loads_by_driver_availability(loads, driver_availability):
    """
    Filter loads based on driver's availability window
    
    Args:
        loads: List of loads from DAT API
        driver_availability: Dict with 'earliestWhen' and 'latestWhen' keys
    
    Returns:
        Filtered list of loads that driver can pickup
    """
    if not driver_availability or not loads:
        return loads
    
    driver_earliest = driver_availability.get('earliestWhen')
    driver_latest = driver_availability.get('latestWhen')
    
    if not driver_earliest and not driver_latest:
        return loads
    
    try:
        from datetime import datetime
        
        # Convert driver availability to datetime objects
        driver_start = None
        driver_end = None
        
        if driver_earliest:
            driver_start = datetime.fromisoformat(driver_earliest.replace('Z', '+00:00'))
        if driver_latest:
            driver_end = datetime.fromisoformat(driver_latest.replace('Z', '+00:00'))
        
        filtered_loads = []
        
        for load in loads:
            load_availability = load.get('availability', {})
            load_earliest = load_availability.get('earliestWhen')
            load_latest = load_availability.get('latestWhen')
            
            if not load_earliest and not load_latest:
                # If load has no availability info, include it
                filtered_loads.append(load)
                continue
            
            # Convert load availability to datetime objects
            load_start = None
            load_end = None
            
            if load_earliest:
                load_start = datetime.fromisoformat(load_earliest.replace('Z', '+00:00'))
            if load_latest:
                load_end = datetime.fromisoformat(load_latest.replace('Z', '+00:00'))
            
            # Check if there's any overlap between driver and load availability
            can_pickup = True
            
            if driver_start and load_end:
                # Driver available after load pickup window ends
                if driver_start > load_end:
                    can_pickup = False
            
            if driver_end and load_start:
                # Driver available before load pickup window starts
                if driver_end < load_start:
                    can_pickup = False
            
            if can_pickup:
                filtered_loads.append(load)
        
        return filtered_loads
        
    except Exception as e:
        print(f"❌ Error filtering loads by availability: {str(e)}")
        return loads  # Return original loads if filtering fails


@app.route('/api/get-loads-for-driver', methods=['POST'])
def get_loads_for_driver():
    """
    Get ranked loads for a selected driver using KAYAAN Profit Score

    Request body:
    {
        "driver_location_city": "Houston",
        "driver_location_state": "TX",
        "equipment_type": "V",
        "driver_availability": {
            "earliestWhen": "2025-10-28T15:00:00Z" (optional),
            "latestWhen": "2025-10-29T06:59:59Z" (optional)
        },
        "filters": {
            "destination_state": "CA" (optional),
            "max_deadhead": 50 (optional),
            "load_type": "FULL" or "PARTIAL" or "BOTH" (optional)
        },
        "limit": 50,
        "environment": "staging" or "production" (optional, defaults to staging),
        "production_credentials": {
            "username": "your_production_username@company.com" (required for production),
            "password": "your_production_password" (required for production),
            "user": "your_production_user@company.com" (required for production)
        } (optional, only needed when environment is "production")
    }
    """
    try:
        data = request.json

        driver_location_city = data.get('driver_location_city')
        driver_location_state = data.get('driver_location_state')
        equipment_type = data.get('equipment_type', 'V')
        driver_availability = data.get('driver_availability', {})
        filters = data.get('filters', {})
        limit = data.get('limit', 50)
        environment = data.get('environment', 'staging')
        production_credentials = data.get('production_credentials')

        # Validate required fields
        if not driver_location_state:
            return jsonify({"error": "driver_location_state is required"}), 400

        # Check if city is provided and not empty
        if not driver_location_city or driver_location_city.strip() == '' or driver_location_city == 'N/A':
            return jsonify({"error": "driver_location_city is required and must be a valid city name"}), 400

        # Get DAT client with specified environment and credentials
        if environment == 'production':
            if production_credentials:
                # Use production credentials from frontend
                username = production_credentials.get('username')
                password = production_credentials.get('password')
                user = production_credentials.get('user')
                
                if not all([username, password, user]):
                    return jsonify({'error': 'Production credentials are required for production environment'}), 400
                
                # Create client with production credentials
                client = DATClient(username=username, password=password, user=user, environment='production')
                if not client.authenticate():
                    return jsonify({'error': 'Failed to authenticate with DAT production using provided credentials'}), 401
            else:
                # Production selected but no credentials provided
                return jsonify({'error': 'Production credentials are required when using Production environment. Please fill in all credential fields in the UI.'}), 400
        else:
            # Use default client (staging)
            client = get_dat_client(environment)

        # Check if city has coordinates in database before searching
        from city_database import get_city_coordinates
        coords = get_city_coordinates(driver_location_city, driver_location_state)
        if not coords:
            return jsonify({
                "error": f"City coordinates not found in database",
                "message": f"Cannot search loads for {driver_location_city}, {driver_location_state}. City coordinates are not available in our database. Please try a driver from a different city."
            }), 400

        # Search for loads from driver's location
        loads = client.search_loads_for_driver(
            driver_location_city=driver_location_city,
            driver_location_state=driver_location_state,
            equipment_type=equipment_type,
            filters=filters,
            limit=limit
        )

        if loads is None:
            return jsonify({"error": "Failed to search loads"}), 500

        if not loads:
            return jsonify({
                "loads": [],
                "total_count": 0,
                "message": "No loads found for this driver location"
            })

        # Filter loads by driver availability if provided
        if driver_availability:
            loads = filter_loads_by_driver_availability(loads, driver_availability)
            print(f"📅 Filtered loads by driver availability: {len(loads)} loads remain")

        # Filter loads by load type if provided
        load_type_filter = filters.get('load_type')
        if load_type_filter and load_type_filter in ['FULL', 'PARTIAL', 'BOTH']:
            loads = filter_loads_by_type(loads, load_type_filter)
            print(f"🚛 Filtered loads by type ({load_type_filter}): {len(loads)} loads remain")

        # Analyze loads using KAYAAN Profit Score
        analyzed_loads = analyze_loads_for_driver(loads, driver_location_state, client)

        # Format for frontend
        formatted_loads = []
        for load in analyzed_loads:
            raw_load = load.get("raw_load", {})
            asset_info = raw_load.get("matchingAssetInfo", {})
            
            poster = raw_load.get("posterInfo", {})
            contact = poster.get("contact", {})
            credit = poster.get("credit", {})
            poster_dot_ids = raw_load.get("posterDotIds", {})
            
            # Get broker USDOT data
            broker_dot_number = poster_dot_ids.get("dotNumber") or "N/A"
            broker_usdot_data = None
            if broker_dot_number and broker_dot_number != "N/A" and broker_dot_number != 0:
                broker_usdot_data = get_usdot_data(str(broker_dot_number))

            formatted_load = {
                "match_id": load.get("match_id", ""),
                "origin": load.get("origin", {}),
                "destination": load.get("destination", {}),
                "profit_data": load.get("profit_data", {}),
                "market_data": load.get("market_data", {}),
                "composite_data": load.get("composite_data", {}),
                "broker_info": {
                    "company_name": poster.get("companyName", "N/A"),
                    "phone": contact.get("phoneNumber") or contact.get("phone") or "N/A",
                    "email": contact.get("email", "N/A"),
                    "mc_number": poster_dot_ids.get("brokerMcNumber") or poster_dot_ids.get("carrierMcNumber") or "N/A",
                    "dot_number": broker_dot_number,
                    "credit_score": credit.get("creditScore") or "N/A",
                    "days_to_pay": credit.get("daysToPay", "N/A"),
                    "usdot_data": broker_usdot_data  # Broker USDOT data (trucks, drivers, etc.)
                },
                "load_details": {
                    "comments": raw_load.get("comments", "N/A"),
                    "is_bookable": raw_load.get("isBookable", False),
                    "is_negotiable": raw_load.get("isNegotiable", False),
                    "posting_id": raw_load.get("postingId", "N/A"),
                    "weight_pounds": (
                        asset_info.get("capacity", {}).get("shipment", {}).get("maximumWeightPounds") or 
                        raw_load.get("maximumWeightPounds") or 
                        asset_info.get("weightPounds") or 
                        "N/A"
                    ),
                    "length_feet": (
                        asset_info.get("capacity", {}).get("shipment", {}).get("maximumLengthFeet") or 
                        raw_load.get("maximumLengthFeet") or 
                        asset_info.get("lengthFeet") or 
                        "N/A"
                    ),
                    "full_partial": (
                        asset_info.get("capacity", {}).get("shipment", {}).get("fullPartial") or 
                        raw_load.get("fullPartial") or 
                        asset_info.get("fullPartial") or 
                        "N/A"
                    ),
                    "commodity": asset_info.get("commodity", "N/A"),
                    "special_instructions": asset_info.get("specialInstructions", "N/A"),
                    "reference_id": asset_info.get("referenceId", "N/A"),
                    "equipment_type": asset_info.get("equipmentType", "N/A")
                },
                "availability": raw_load.get("availability", {}),
                "reference_number": asset_info.get("referenceId", "N/A")
            }

            formatted_loads.append(formatted_load)

        return jsonify({
            "loads": formatted_loads,
            "total_count": len(formatted_loads),
            "analyzed_with": "KAYAAN Profit Score"
        })

    except Exception as e:
        print(f"Error in get_loads_for_driver: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/')
def index():
    """Serve the frontend HTML"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
    return send_file(frontend_path)


@app.route('/api/cities/<state>', methods=['GET'])
def get_cities(state):
    """Get list of cities for a state"""
    try:
        cities = get_cities_by_state(state.upper())
        return jsonify({
            "state": state.upper(),
            "cities": [city["name"] for city in cities]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/states', methods=['GET'])
def get_states():
    """Get list of all US states"""
    states = [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
    ]
    return jsonify({"states": states})


@app.route('/api/authenticate', methods=['POST'])
def test_authentication():
    """Test DAT authentication"""
    try:
        data = request.json or {}
        environment = data.get('environment', 'staging')
        client = get_dat_client(environment)
        return jsonify({
            "success": True,
            "message": "Authentication successful",
            "api_calls": client.api_calls
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Driver GTM API"})


if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Driver GTM API Server")
    print("=" * 80)
    print(f"   Port: 5004")
    print(f"   Environment: Staging")
    print("=" * 80)
    print("\nEndpoints:")
    print("   POST /api/search-drivers - Search for available drivers")
    print("   POST /api/get-loads-for-driver - Get ranked loads for driver")
    print("   GET  /api/cities/<state> - Get cities for state")
    print("   GET  /api/states - Get all US states")
    print("   POST /api/authenticate - Test DAT authentication")
    print("   GET  /health - Health check")
    print("=" * 80)

    app.run(debug=True, host='0.0.0.0', port=5004)
