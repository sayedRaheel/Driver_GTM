#!/usr/bin/env python3
"""
City Database with Coordinates for DAT API
Major cities by state with lat/lng coordinates
"""

MAJOR_CITIES = {
    "AL": [
        {"name": "Birmingham", "lat": 33.5186, "lng": -86.8104},
        {"name": "Mobile", "lat": 30.6954, "lng": -88.0399},
        {"name": "Montgomery", "lat": 32.3617, "lng": -86.2792},
        {"name": "Huntsville", "lat": 34.7304, "lng": -86.5861}
    ],
    "AK": [
        {"name": "Anchorage", "lat": 61.2181, "lng": -149.9003},
        {"name": "Fairbanks", "lat": 64.8378, "lng": -147.7164}
    ],
    "AZ": [
        {"name": "Phoenix", "lat": 33.4484, "lng": -112.0740},
        {"name": "Tucson", "lat": 32.2226, "lng": -110.9747},
        {"name": "Mesa", "lat": 33.4152, "lng": -111.8315},
        {"name": "Flagstaff", "lat": 35.1983, "lng": -111.6513}
    ],
    "AR": [
        {"name": "Little Rock", "lat": 34.7465, "lng": -92.2896},
        {"name": "Fort Smith", "lat": 35.3859, "lng": -94.3985},
        {"name": "Fayetteville", "lat": 36.0626, "lng": -94.1574}
    ],
    "CA": [
        {"name": "Los Angeles", "lat": 34.0522, "lng": -118.2437},
        {"name": "San Francisco", "lat": 37.7749, "lng": -122.4194},
        {"name": "San Diego", "lat": 32.7157, "lng": -117.1611},
        {"name": "Sacramento", "lat": 38.5816, "lng": -121.4944},
        {"name": "Fresno", "lat": 36.7378, "lng": -119.7871},
        {"name": "Oakland", "lat": 37.8044, "lng": -122.2712},
        {"name": "Bakersfield", "lat": 35.3733, "lng": -119.0187},
        {"name": "Long Beach", "lat": 33.7701, "lng": -118.1937}
    ],
    "CO": [
        {"name": "Denver", "lat": 39.7392, "lng": -104.9903},
        {"name": "Colorado Springs", "lat": 38.8339, "lng": -104.8214},
        {"name": "Aurora", "lat": 39.7294, "lng": -104.8319},
        {"name": "Fort Collins", "lat": 40.5853, "lng": -105.0844}
    ],
    "CT": [
        {"name": "Hartford", "lat": 41.7658, "lng": -72.6734},
        {"name": "Bridgeport", "lat": 41.1865, "lng": -73.1952},
        {"name": "New Haven", "lat": 41.3083, "lng": -72.9279}
    ],
    "DE": [
        {"name": "Wilmington", "lat": 39.7391, "lng": -75.5398},
        {"name": "Dover", "lat": 39.1612, "lng": -75.5264}
    ],
    "FL": [
        {"name": "Miami", "lat": 25.7617, "lng": -80.1918},
        {"name": "Tampa", "lat": 27.9506, "lng": -82.4572},
        {"name": "Orlando", "lat": 28.5383, "lng": -81.3792},
        {"name": "Jacksonville", "lat": 30.3322, "lng": -81.6557},
        {"name": "St. Petersburg", "lat": 27.7676, "lng": -82.6404},
        {"name": "Fort Lauderdale", "lat": 26.1224, "lng": -80.1373},
        {"name": "Tallahassee", "lat": 30.4518, "lng": -84.27277}
    ],
    "GA": [
        {"name": "Atlanta", "lat": 33.7490, "lng": -84.3880},
        {"name": "Augusta", "lat": 33.4735, "lng": -82.0105},
        {"name": "Columbus", "lat": 32.4609, "lng": -84.9877},
        {"name": "Savannah", "lat": 32.0835, "lng": -81.0998},
        {"name": "Macon", "lat": 32.8407, "lng": -83.6324}
    ],
    "HI": [
        {"name": "Honolulu", "lat": 21.3099, "lng": -157.8581}
    ],
    "ID": [
        {"name": "Boise", "lat": 43.6150, "lng": -116.2023},
        {"name": "Idaho Falls", "lat": 43.4927, "lng": -112.0362}
    ],
    "IL": [
        {"name": "Chicago", "lat": 41.8781, "lng": -87.6298},
        {"name": "Aurora", "lat": 41.7606, "lng": -88.3201},
        {"name": "Peoria", "lat": 40.6936, "lng": -89.5890},
        {"name": "Rockford", "lat": 42.2711, "lng": -89.0940},
        {"name": "Springfield", "lat": 39.7817, "lng": -89.6501}
    ],
    "IN": [
        {"name": "Indianapolis", "lat": 39.7684, "lng": -86.1581},
        {"name": "Fort Wayne", "lat": 41.0793, "lng": -85.1394},
        {"name": "Evansville", "lat": 37.9716, "lng": -87.5710},
        {"name": "South Bend", "lat": 41.6764, "lng": -86.2520}
    ],
    "IA": [
        {"name": "Des Moines", "lat": 41.5868, "lng": -93.6250},
        {"name": "Cedar Rapids", "lat": 41.9779, "lng": -91.6656},
        {"name": "Davenport", "lat": 41.5236, "lng": -90.5776}
    ],
    "KS": [
        {"name": "Wichita", "lat": 37.6872, "lng": -97.3301},
        {"name": "Overland Park", "lat": 38.9822, "lng": -94.6708},
        {"name": "Kansas City", "lat": 39.1142, "lng": -94.6275},
        {"name": "Topeka", "lat": 39.0473, "lng": -95.6890}
    ],
    "KY": [
        {"name": "Louisville", "lat": 38.2527, "lng": -85.7585},
        {"name": "Lexington", "lat": 38.0406, "lng": -84.5037},
        {"name": "Bowling Green", "lat": 36.9685, "lng": -86.4808}
    ],
    "LA": [
        {"name": "New Orleans", "lat": 29.9511, "lng": -90.0715},
        {"name": "Baton Rouge", "lat": 30.4515, "lng": -91.1871},
        {"name": "Shreveport", "lat": 32.5252, "lng": -93.7502},
        {"name": "Lafayette", "lat": 30.2241, "lng": -92.0198}
    ],
    "ME": [
        {"name": "Portland", "lat": 43.6591, "lng": -70.2568},
        {"name": "Lewiston", "lat": 44.1003, "lng": -70.2148}
    ],
    "MD": [
        {"name": "Baltimore", "lat": 39.2904, "lng": -76.6122},
        {"name": "Frederick", "lat": 39.4143, "lng": -77.4105},
        {"name": "Gaithersburg", "lat": 39.1434, "lng": -77.2014}
    ],
    "MA": [
        {"name": "Boston", "lat": 42.3601, "lng": -71.0589},
        {"name": "Worcester", "lat": 42.2626, "lng": -71.8023},
        {"name": "Springfield", "lat": 42.1015, "lng": -72.5898}
    ],
    "MI": [
        {"name": "Detroit", "lat": 42.3314, "lng": -83.0458},
        {"name": "Grand Rapids", "lat": 42.9634, "lng": -85.6681},
        {"name": "Warren", "lat": 42.5145, "lng": -83.0146},
        {"name": "Sterling Heights", "lat": 42.5803, "lng": -83.0302}
    ],
    "MN": [
        {"name": "Minneapolis", "lat": 44.9778, "lng": -93.2650},
        {"name": "Saint Paul", "lat": 44.9537, "lng": -93.0900},
        {"name": "Rochester", "lat": 44.0121, "lng": -92.4802},
        {"name": "Duluth", "lat": 46.7867, "lng": -92.1005}
    ],
    "MS": [
        {"name": "Jackson", "lat": 32.2988, "lng": -90.1848},
        {"name": "Gulfport", "lat": 30.3674, "lng": -89.0928},
        {"name": "Southaven", "lat": 34.9890, "lng": -90.0262}
    ],
    "MO": [
        {"name": "Kansas City", "lat": 39.0997, "lng": -94.5786},
        {"name": "St. Louis", "lat": 38.6270, "lng": -90.1994},
        {"name": "Springfield", "lat": 37.2153, "lng": -93.2982},
        {"name": "Columbia", "lat": 38.9517, "lng": -92.3341}
    ],
    "MT": [
        {"name": "Billings", "lat": 45.7833, "lng": -108.5007},
        {"name": "Missoula", "lat": 46.8721, "lng": -113.9940}
    ],
    "NE": [
        {"name": "Omaha", "lat": 41.2565, "lng": -95.9345},
        {"name": "Lincoln", "lat": 40.8136, "lng": -96.7026},
        {"name": "Bellevue", "lat": 41.1370, "lng": -95.9145}
    ],
    "NV": [
        {"name": "Las Vegas", "lat": 36.1699, "lng": -115.1398},
        {"name": "Henderson", "lat": 36.0397, "lng": -114.9817},
        {"name": "Reno", "lat": 39.5296, "lng": -119.8138}
    ],
    "NH": [
        {"name": "Manchester", "lat": 42.9956, "lng": -71.4548},
        {"name": "Nashua", "lat": 42.7654, "lng": -71.4676}
    ],
    "NJ": [
        {"name": "Newark", "lat": 40.7357, "lng": -74.1724},
        {"name": "Jersey City", "lat": 40.7178, "lng": -74.0431},
        {"name": "Paterson", "lat": 40.9168, "lng": -74.1718},
        {"name": "Elizabeth", "lat": 40.6640, "lng": -74.2107},
        {"name": "Edison", "lat": 40.5187, "lng": -74.4121},
        {"name": "Woodbridge", "lat": 40.5576, "lng": -74.2846},
        {"name": "Lakewood", "lat": 40.0979, "lng": -74.2176},
        {"name": "Toms River", "lat": 39.9537, "lng": -74.1979},
        {"name": "Hamilton", "lat": 40.2298, "lng": -74.6751},
        {"name": "Trenton", "lat": 40.2171, "lng": -74.7429},
        {"name": "Clifton", "lat": 40.8584, "lng": -74.1638},
        {"name": "Camden", "lat": 39.9259, "lng": -75.1196},
        {"name": "Brick", "lat": 40.0576, "lng": -74.1035},
        {"name": "Cherry Hill", "lat": 39.9350, "lng": -75.0307},
        {"name": "Passaic", "lat": 40.8568, "lng": -74.1285},
        {"name": "Union City", "lat": 40.6976, "lng": -74.0260},
        {"name": "Bayonne", "lat": 40.6687, "lng": -74.1143},
        {"name": "East Orange", "lat": 40.7674, "lng": -74.2049},
        {"name": "Vineland", "lat": 39.4864, "lng": -75.0254},
        {"name": "New Brunswick", "lat": 40.4862, "lng": -74.4518},
        {"name": "Hoboken", "lat": 40.7439, "lng": -74.0324},
        {"name": "Perth Amboy", "lat": 40.5067, "lng": -74.2654},
        {"name": "West New York", "lat": 40.7879, "lng": -74.0143},
        {"name": "Plainfield", "lat": 40.6337, "lng": -74.4074},
        {"name": "Hackensack", "lat": 40.8859, "lng": -74.0435},
        {"name": "Sayreville", "lat": 40.4593, "lng": -74.3610},
        {"name": "Kearny", "lat": 40.7684, "lng": -74.1454},
        {"name": "Linden", "lat": 40.6220, "lng": -74.2446},
        {"name": "Atlantic City", "lat": 39.3643, "lng": -74.4229},
        {"name": "Fort Lee", "lat": 40.8509, "lng": -73.9701},
        {"name": "Fair Lawn", "lat": 40.9403, "lng": -74.1318},
        {"name": "Garfield", "lat": 40.8815, "lng": -74.1132},
        {"name": "Totowa", "lat": 40.9051, "lng": -74.2099},
        {"name": "Morganville", "lat": 40.3751, "lng": -74.2510},
        {"name": "Monmouth Junction", "lat": 40.3896, "lng": -74.5488}
    ],
    "NM": [
        {"name": "Albuquerque", "lat": 35.0844, "lng": -106.6504},
        {"name": "Las Cruces", "lat": 32.3199, "lng": -106.7637},
        {"name": "Rio Rancho", "lat": 35.2328, "lng": -106.6630}
    ],
    "NY": [
        {"name": "New York City", "lat": 40.7128, "lng": -74.0060},
        {"name": "Buffalo", "lat": 42.8864, "lng": -78.8784},
        {"name": "Rochester", "lat": 43.1566, "lng": -77.6088},
        {"name": "Yonkers", "lat": 40.9312, "lng": -73.8988},
        {"name": "Syracuse", "lat": 43.0389, "lng": -76.1351},
        {"name": "Albany", "lat": 42.6526, "lng": -73.7562}
    ],
    "NC": [
        {"name": "Charlotte", "lat": 35.2271, "lng": -80.8431},
        {"name": "Raleigh", "lat": 35.7796, "lng": -78.6382},
        {"name": "Greensboro", "lat": 36.0726, "lng": -79.7920},
        {"name": "Durham", "lat": 35.9940, "lng": -78.8986},
        {"name": "Winston-Salem", "lat": 36.0999, "lng": -80.2442}
    ],
    "ND": [
        {"name": "Fargo", "lat": 46.8772, "lng": -96.7898},
        {"name": "Bismarck", "lat": 46.8083, "lng": -100.7837}
    ],
    "OH": [
        {"name": "Columbus", "lat": 39.9612, "lng": -82.9988},
        {"name": "Cleveland", "lat": 41.4993, "lng": -81.6944},
        {"name": "Cincinnati", "lat": 39.1031, "lng": -84.5120},
        {"name": "Toledo", "lat": 41.6528, "lng": -83.5379},
        {"name": "Akron", "lat": 41.0814, "lng": -81.5190},
        {"name": "Dayton", "lat": 39.7589, "lng": -84.1916}
    ],
    "OK": [
        {"name": "Oklahoma City", "lat": 35.4676, "lng": -97.5164},
        {"name": "Tulsa", "lat": 36.1540, "lng": -95.9928},
        {"name": "Norman", "lat": 35.2226, "lng": -97.4395}
    ],
    "OR": [
        {"name": "Portland", "lat": 45.5152, "lng": -122.6784},
        {"name": "Salem", "lat": 44.9429, "lng": -123.0351},
        {"name": "Eugene", "lat": 44.0521, "lng": -123.0868}
    ],
    "PA": [
        {"name": "Philadelphia", "lat": 39.9526, "lng": -75.1652},
        {"name": "Pittsburgh", "lat": 40.4406, "lng": -79.9959},
        {"name": "Allentown", "lat": 40.6084, "lng": -75.4902},
        {"name": "Erie", "lat": 42.1292, "lng": -80.0851},
        {"name": "Reading", "lat": 40.3356, "lng": -75.9269}
    ],
    "RI": [
        {"name": "Providence", "lat": 41.8240, "lng": -71.4128},
        {"name": "Cranston", "lat": 41.7798, "lng": -71.4371}
    ],
    "SC": [
        {"name": "Charleston", "lat": 32.7765, "lng": -79.9311},
        {"name": "Columbia", "lat": 34.0007, "lng": -81.0348},
        {"name": "North Charleston", "lat": 32.8546, "lng": -79.9748}
    ],
    "SD": [
        {"name": "Sioux Falls", "lat": 43.5446, "lng": -96.7311},
        {"name": "Rapid City", "lat": 44.0805, "lng": -103.2310}
    ],
    "TN": [
        {"name": "Nashville", "lat": 36.1627, "lng": -86.7816},
        {"name": "Memphis", "lat": 35.1495, "lng": -90.0490},
        {"name": "Knoxville", "lat": 35.9606, "lng": -83.9207},
        {"name": "Chattanooga", "lat": 35.0456, "lng": -85.3097}
    ],
    "TX": [
        {"name": "Houston", "lat": 29.7604, "lng": -95.3698},
        {"name": "Dallas", "lat": 32.7767, "lng": -96.7970},
        {"name": "San Antonio", "lat": 29.4241, "lng": -98.4936},
        {"name": "Austin", "lat": 30.2672, "lng": -97.7431},
        {"name": "Fort Worth", "lat": 32.7555, "lng": -97.3308},
        {"name": "El Paso", "lat": 31.7619, "lng": -106.4850},
        {"name": "Arlington", "lat": 32.7357, "lng": -97.1081},
        {"name": "Corpus Christi", "lat": 27.8006, "lng": -97.3964},
        {"name": "Plano", "lat": 33.0198, "lng": -96.6989},
        {"name": "Lubbock", "lat": 33.5779, "lng": -101.8552},
        {"name": "Laredo", "lat": 27.5306, "lng": -99.4803},
        {"name": "Irving", "lat": 32.8140, "lng": -96.9489},
        {"name": "Garland", "lat": 32.9126, "lng": -96.6389},
        {"name": "Frisco", "lat": 33.1507, "lng": -96.8236},
        {"name": "McKinney", "lat": 33.1972, "lng": -96.6154},
        {"name": "Grand Prairie", "lat": 32.7460, "lng": -96.9978},
        {"name": "Mesquite", "lat": 32.7668, "lng": -96.5991},
        {"name": "Amarillo", "lat": 35.2220, "lng": -101.8313},
        {"name": "Killeen", "lat": 31.1171, "lng": -97.7278},
        {"name": "McAllen", "lat": 26.2034, "lng": -98.2300}
    ],
    "UT": [
        {"name": "Salt Lake City", "lat": 40.7608, "lng": -111.8910},
        {"name": "West Valley City", "lat": 40.6916, "lng": -112.0010},
        {"name": "Provo", "lat": 40.2338, "lng": -111.6585},
        {"name": "West Jordan", "lat": 40.6097, "lng": -111.9391}
    ],
    "VT": [
        {"name": "Burlington", "lat": 44.4759, "lng": -73.2121},
        {"name": "Essex", "lat": 44.4906, "lng": -73.1129}
    ],
    "VA": [
        {"name": "Virginia Beach", "lat": 36.8529, "lng": -75.9780},
        {"name": "Norfolk", "lat": 36.8468, "lng": -76.2852},
        {"name": "Chesapeake", "lat": 36.7682, "lng": -76.2875},
        {"name": "Richmond", "lat": 37.5407, "lng": -77.4360},
        {"name": "Newport News", "lat": 37.0871, "lng": -76.4730}
    ],
    "WA": [
        {"name": "Seattle", "lat": 47.6062, "lng": -122.3321},
        {"name": "Spokane", "lat": 47.6587, "lng": -117.4260},
        {"name": "Tacoma", "lat": 47.2529, "lng": -122.4443},
        {"name": "Vancouver", "lat": 45.6387, "lng": -122.6615},
        {"name": "Bellevue", "lat": 47.6101, "lng": -122.2015}
    ],
    "WV": [
        {"name": "Charleston", "lat": 38.3498, "lng": -81.6326},
        {"name": "Huntington", "lat": 38.4192, "lng": -82.4452}
    ],
    "WI": [
        {"name": "Milwaukee", "lat": 43.0389, "lng": -87.9065},
        {"name": "Madison", "lat": 43.0731, "lng": -89.4012},
        {"name": "Green Bay", "lat": 44.5133, "lng": -88.0133},
        {"name": "Kenosha", "lat": 42.5847, "lng": -87.8212}
    ],
    "WY": [
        {"name": "Cheyenne", "lat": 41.1400, "lng": -104.8197},
        {"name": "Casper", "lat": 42.8666, "lng": -106.3131}
    ]
}

def get_cities_by_state(state_code):
    """Get all cities for a given state"""
    return MAJOR_CITIES.get(state_code.upper(), [])

def get_city_coordinates(city_name, state_code):
    """Get coordinates for a specific city and state with online fallback"""
    cities = get_cities_by_state(state_code)

    # First try exact match
    for city in cities:
        if city["name"].lower() == city_name.lower():
            return {"lat": city["lat"], "lng": city["lng"]}

    # Try common abbreviations and partial matches
    city_lower = city_name.lower()

    # Handle common abbreviations
    abbreviations = {
        "jct": "junction",
        "junct": "junction",
        "ft": "fort",
        "st": "saint",
        "mt": "mount"
    }

    # Expand abbreviations in the search term
    for abbrev, full in abbreviations.items():
        # Check if city starts with abbreviation + space (e.g., "Ft Lee")
        if city_lower.startswith(f"{abbrev} "):
            expanded = city_lower.replace(f"{abbrev} ", f"{full} ", 1)
            for city in cities:
                if city["name"].lower() == expanded:
                    return {"lat": city["lat"], "lng": city["lng"]}
        # Check if abbreviation is in the middle or at end
        if f" {abbrev}" in city_lower or city_lower.endswith(abbrev):
            expanded = city_lower.replace(f" {abbrev}", f" {full}")
            for city in cities:
                if city["name"].lower() == expanded:
                    return {"lat": city["lat"], "lng": city["lng"]}

    # Try partial match (beginning of city name)
    for city in cities:
        if city["name"].lower().startswith(city_lower) or city_lower.startswith(city["name"].lower()):
            return {"lat": city["lat"], "lng": city["lng"]}

    # If not found in database, try online geocoding as fallback
    try:
        import requests
        import time

        # Use Nominatim (OpenStreetMap) API - free and no API key required
        # Format: city, state, USA
        query = f"{city_name}, {state_code}, USA"
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "countrycodes": "us"
        }
        headers = {
            "User-Agent": "DriverGTM/1.0"  # Nominatim requires a user agent
        }

        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                lat = float(result["lat"])
                lng = float(result["lon"])
                print(f"📍 Online geocoding: {city_name}, {state_code} → {lat:.4f}, {lng:.4f}")
                time.sleep(1)  # Rate limiting - Nominatim allows 1 request per second
                return {"lat": lat, "lng": lng}
    except Exception as e:
        print(f"⚠️  Online geocoding failed for {city_name}, {state_code}: {str(e)}")

    return None

def get_all_states():
    """Get all available states"""
    return sorted(MAJOR_CITIES.keys())

def validate_city_state(city_name, state_code):
    """Validate if city exists in the given state"""
    coordinates = get_city_coordinates(city_name, state_code)
    return coordinates is not None

if __name__ == "__main__":
    # Test the database
    print("🏙️ Testing City Database")
    print(f"Available states: {len(get_all_states())}")
    print(f"Texas cities: {len(get_cities_by_state('TX'))}")
    
    # Test Houston coordinates
    houston_coords = get_city_coordinates("Houston", "TX")
    print(f"Houston coordinates: {houston_coords}")
    
    # Test validation
    is_valid = validate_city_state("Houston", "TX")
    print(f"Houston, TX is valid: {is_valid}")