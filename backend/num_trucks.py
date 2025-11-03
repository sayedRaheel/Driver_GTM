import requests
import json
import os
from typing import Optional, Dict

# USDOT API Configuration
USDOT_BASE_URL = "https://data.transportation.gov/resource/az4n-8mr2.json"
# USDOT tokens - set via environment variables (USDOT_APP_TOKEN, USDOT_SECRET_TOKEN)
# If not set, these will be None and API calls may fail
APP_TOKEN = os.getenv("USDOT_APP_TOKEN")
SECRET_TOKEN = os.getenv("USDOT_SECRET_TOKEN")

# Cache to avoid repeated API calls (simple in-memory cache)
# This cache persists for the lifetime of the Python process
_truck_count_cache = {}
_usdot_data_cache = {}

def get_usdot_data(dot_number: str) -> Optional[Dict]:
    """
    Get full company data from USDOT API by DOT number
    
    Args:
        dot_number: DOT number as string
        
    Returns:
        Dict with company data or None if not found or error
        Fields: dot_number, legal_name, truck_units, total_drivers, phy_city, phy_state, mc_number, entity_type
    """
    if not dot_number or dot_number == "N/A" or dot_number == 0:
        return None
    
    dot_str = str(dot_number).strip()
    
    # Check cache first
    if dot_str in _usdot_data_cache:
        return _usdot_data_cache[dot_str]
    
    try:
        if not APP_TOKEN:
            print(f"⚠️  USDOT_APP_TOKEN not set in environment variables")
            return None
            
        headers = {
            "Accept": "application/json",
            "X-App-Token": APP_TOKEN,
        }
        
        params = {
            "dot_number": dot_str
        }
        
        response = requests.get(USDOT_BASE_URL, headers=headers, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                print(f"📋 USDOT API returned {len(data)} record(s) for DOT {dot_str}")
                result = data[0]
                # Parse MC number from docket fields
                mc_number = None
                if result.get("docket1prefix") and result.get("docket1"):
                    if str(result.get("docket1prefix")).upper() == "MC":
                        try:
                            mc_number = int(result.get("docket1"))
                        except (ValueError, TypeError):
                            pass
                
                # Parse truck_units and total_drivers safely (API returns as strings)
                truck_units = None
                total_drivers = None
                try:
                    truck_units_val = result.get("truck_units")
                    if truck_units_val is not None and truck_units_val != "":
                        # Handle both string and int values
                        truck_units = int(str(truck_units_val))
                except (ValueError, TypeError) as e:
                    print(f"⚠️  Could not parse truck_units '{result.get('truck_units')}': {str(e)}")
                    pass
                    
                try:
                    total_drivers_val = result.get("total_drivers")
                    if total_drivers_val is not None and total_drivers_val != "":
                        # Handle both string and int values
                        total_drivers = int(str(total_drivers_val))
                except (ValueError, TypeError) as e:
                    print(f"⚠️  Could not parse total_drivers '{result.get('total_drivers')}': {str(e)}")
                    pass
                
                usdot_data = {
                    "dot_number": result.get("dot_number"),
                    "legal_name": result.get("legal_name"),
                    "truck_units": truck_units,
                    "total_drivers": total_drivers,
                    "phy_city": result.get("phy_city"),
                    "phy_state": result.get("phy_state"),
                    "mc_number": mc_number,
                    "entity_type": result.get("entity_type")
                }
                
                # Cache the result
                _usdot_data_cache[dot_str] = usdot_data
                print(f"📊 USDOT data fetched for DOT {dot_str}: {usdot_data.get('truck_units', 'N/A')} trucks")
                return usdot_data
        
        # If no data found, cache as None
        print(f"⚠️  USDOT API returned status {response.status_code} or no data for DOT {dot_str}")
        if response.status_code != 200:
            print(f"   Response text: {response.text[:200]}")
        _usdot_data_cache[dot_str] = None
        return None
        
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout fetching USDOT data for DOT {dot_str}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching USDOT data for DOT {dot_str}: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error fetching USDOT data for DOT {dot_str}: {str(e)}")
        return None

def get_truck_count(dot_number: str) -> Optional[int]:
    """
    Get truck count for a company by DOT number from USDOT API
    (Backward compatibility wrapper - uses get_usdot_data)
    
    Args:
        dot_number: DOT number as string
        
    Returns:
        Truck count (int) or None if not found or error
    """
    data = get_usdot_data(dot_number)
    if data:
        truck_count = data.get("truck_units")
        # Also cache in old format for backward compatibility
        if truck_count is not None:
            dot_str = str(dot_number).strip()
            _truck_count_cache[dot_str] = truck_count
        return truck_count
    return None

def clear_cache():
    """Clear all caches"""
    global _truck_count_cache, _usdot_data_cache
    _truck_count_cache.clear()
    _usdot_data_cache.clear()
    print("🗑️  All caches cleared")

def get_cache_stats():
    """Get cache statistics"""
    return {
        "cached_count": len(_truck_count_cache),
        "cached_dots": list(_truck_count_cache.keys())
    }
