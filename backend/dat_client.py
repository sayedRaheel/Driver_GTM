#!/usr/bin/env python3
"""
Driver GTM - DAT API Client
Handles capacity search (drivers) and load search with efRouting scoring
"""

import requests
import json
import time
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

try:
    from city_database import get_city_coordinates
except ImportError:
    def get_city_coordinates(city, state):
        return None

class DATClient:
    """DAT API client for Driver GTM system"""

    def __init__(self, username: str, password: str, user: str, environment: str = 'production'):
        """
        Initialize DAT client with 3 credentials

        Args:
            username: DAT username (email) for org token
            password: DAT password for org token
            user: DAT user (email) for user token
            environment: 'staging' or 'production'
        """
        self.username = username
        self.password = password
        self.dat_user = user
        self.environment = environment

        # Set API URLs based on environment
        if environment == 'production':
            self.auth_url = "https://identity.api.dat.com/access/v1/token"
            self.freight_url = "https://freight.api.prod.dat.com"
        else:  # staging
            self.auth_url = "https://identity.api.staging.dat.com/access/v1/token"
            self.freight_url = "https://freight.api.staging.dat.com"

        # Tokens
        self.org_token = None
        self.access_token = None  # user token
        self.token_expires_at = 0

        # API call tracking
        self.api_calls = 0
        self.session = requests.Session()

    def authenticate(self) -> bool:
        """
        2-step authentication (org token → user token)
        Returns True if successful
        """
        current_time = time.time()

        # Check if user token is still valid
        if self.access_token and current_time < self.token_expires_at:
            remaining_minutes = (self.token_expires_at - current_time) / 60
            print(f"♻️ Using cached user token (expires in {remaining_minutes:.1f} minutes)")
            return True

        print(f"🔐 Authenticating with DAT {self.environment} environment...")

        try:
            # Step 1: Get organization token
            if not self.org_token:
                org_payload = {
                    "username": self.username,
                    "password": self.password
                }

                org_url = f"{self.auth_url}/organization"
                headers = {"Content-Type": "application/json"}

                self.api_calls += 1
                response = self.session.post(org_url, headers=headers, data=json.dumps(org_payload))
                print(f"📞 API Call #{self.api_calls}: Organization Token")

                if response.status_code == 200:
                    org_data = response.json()
                    self.org_token = org_data.get("accessToken")
                    print("✅ Organization token obtained")
                else:
                    print(f"❌ Organization authentication failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
            else:
                print("♻️ Using cached organization token")

            # Step 2: Get user token
            user_payload = {"username": self.dat_user}
            user_url = f"{self.auth_url}/user"
            user_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.org_token}"
            }

            self.api_calls += 1
            user_response = self.session.post(user_url, headers=user_headers, data=json.dumps(user_payload))
            print(f"📞 API Call #{self.api_calls}: User Token")

            if user_response.status_code == 200:
                user_data = user_response.json()
                self.access_token = user_data.get("accessToken")
                expires_in = user_data.get("expiresIn", 900)  # Default 15 min
                self.token_expires_at = current_time + expires_in
                print(f"✅ User token obtained (expires in {expires_in}s)")
                return True

            print(f"❌ User authentication failed: {user_response.status_code}")
            print(f"   Response: {user_response.text}")
            return False

        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False

    def search_drivers(
        self,
        origin_city: str = None,
        origin_state: str = None,
        equipment_types: List[str] = None,
        filters: Dict = None,
        limit: int = 10
    ) -> Tuple[Optional[List[Dict]], int]:
        """
        Search for drivers/capacity (trucks available for hire)

        Args:
            origin_city: City to search in
            origin_state: State to search in
            equipment_types: List of equipment types (e.g., ["V", "R", "F"])
            filters: Additional filters (availability, destination, deadhead, etc.)
            limit: Number of results to return

        Returns:
            (drivers_list, total_count) tuple
        """
        # Check and refresh authentication if needed (authenticate() handles token refresh automatically)
        # This is safe to call - it will use cached token if still valid, or refresh if expired
        # Only check if we don't have a valid token to avoid unnecessary calls
        current_time = time.time()
        needs_auth = not self.access_token or current_time >= self.token_expires_at
        
        if needs_auth:
            try:
                auth_result = self.authenticate()
                if not auth_result:
                    print("❌ Failed to authenticate - cannot search drivers")
                    return None, 0
            except Exception as auth_error:
                print(f"❌ Authentication error in search_drivers: {str(auth_error)}")
                import traceback
                traceback.print_exc()
                return None, 0

        try:
            # Build base criteria
            criteria = {
                "lane": {
                    "assetType": "TRUCK",  # Search for drivers/capacity
                    "equipment": {"types": equipment_types or ["V"]},
                    "destination": {"open": {}}
                },
                "maxAgeMinutes": 2880,  # 48 hours
                "audience": {
                    "includeLoadBoard": True,
                    "includePrivateNetwork": True
                },
                "countsOnly": False,
                "includeOpenDestinationTrucks": True
            }

            # Add origin location if provided
            if origin_city and origin_state:
                coords = get_city_coordinates(origin_city, origin_state)
                if coords:
                    criteria["lane"]["origin"] = {
                        "place": {
                            "city": origin_city,
                            "stateProv": origin_state,
                            "latitude": coords["lat"],
                            "longitude": coords["lng"]
                        }
                    }
                    print(f"✅ Added coordinates for {origin_city}, {origin_state}: {coords['lat']:.4f}, {coords['lng']:.4f}")
            elif origin_state:
                # State-level search
                criteria["lane"]["origin"] = {"area": {"states": [origin_state]}}

            # Apply filters if provided
            if filters:
                # Availability date filter
                if filters.get("availability_start") or filters.get("availability_end"):
                    availability = {}
                    if filters.get("availability_start"):
                        availability["earliestWhen"] = filters["availability_start"]
                    if filters.get("availability_end"):
                        availability["latestWhen"] = filters["availability_end"]
                    criteria["availability"] = availability

                # Preferred destination filter
                if filters.get("destination_state"):
                    criteria["lane"]["destination"] = {
                        "area": {"states": [filters["destination_state"]]}
                    }

                # Deadhead radius filter
                if filters.get("max_deadhead"):
                    criteria["maxOriginDeadheadMiles"] = filters["max_deadhead"]

            payload = {"criteria": criteria}

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }

            self.api_calls += 1
            print(f"📞 API Call #{self.api_calls}: Search Drivers/Capacity")
            print(f"📋 Query payload: {json.dumps(payload, indent=2)}")

            response = self.session.post(
                f"{self.freight_url}/search/v3/queries",
                json=payload,
                headers=headers
            )

            if response.status_code != 201:
                error_text = response.text[:500]  # Limit error text length
                print(f"❌ Driver search query creation failed: HTTP {response.status_code}")
                print(f"   Response: {error_text}")
                if response.status_code == 401:
                    print("   ⚠️  Authentication expired - token may need refresh")
                elif response.status_code == 400:
                    print("   ⚠️  Invalid request parameters")
                return None, 0

            data = response.json()
            query_id = data.get("queryId")

            if not query_id:
                print("❌ No query ID received from DAT API")
                print(f"   Response data: {data}")
                return None, 0

            print(f"✅ Query created: {query_id}")

            # Get results
            self.api_calls += 1
            print(f"📞 API Call #{self.api_calls}: Get Driver Results")

            match_response = self.session.get(
                f"{self.freight_url}/search/v3/queryMatches/{query_id}",
                headers=headers,
                params={"limit": limit}
            )

            if match_response.status_code != 200:
                error_text = match_response.text[:500]  # Limit error text length
                print(f"❌ Failed to get driver results: HTTP {match_response.status_code}")
                print(f"   Response: {error_text}")
                if match_response.status_code == 404:
                    print("   ⚠️  Query not found - may have expired or been invalid")
                elif match_response.status_code == 401:
                    print("   ⚠️  Authentication expired during results fetch")
                return None, 0

            match_data = match_response.json()
            drivers = match_data.get("matches", [])

            # Get total count from matchCounts
            match_counts = match_data.get("matchCounts", {})
            total_count = (
                match_counts.get("normal", 0) +
                match_counts.get("preferred", 0) +
                match_counts.get("privateNetwork", 0)
            )

            if len(drivers) == 0:
                print(f"⚠️  No drivers found (total available: {total_count})")
            else:
                print(f"✅ Found {len(drivers)} drivers (total: {total_count})")
            
            return drivers, total_count

        except Exception as e:
            print(f"❌ Driver search error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, 0

    def search_loads_for_driver(
        self,
        driver_location_city: str,
        driver_location_state: str,
        equipment_type: str,
        filters: Dict = None,
        limit: int = 50
    ) -> Optional[List[Dict]]:
        """
        Search for loads available from driver's location

        Args:
            driver_location_city: Driver's current city
            driver_location_state: Driver's current state
            equipment_type: Equipment type (e.g., "V", "R", "F")
            filters: Additional filters (destination, max_deadhead, etc.)
            limit: Number of results to return

        Returns:
            List of loads
        """
        if not self.access_token:
            print("❌ Not authenticated")
            return None

        try:
            # Get coordinates for driver location
            coords = get_city_coordinates(driver_location_city, driver_location_state)
            if not coords:
                print(f"❌ Could not get coordinates for {driver_location_city}, {driver_location_state}")
                return None

            # Build criteria for load search
            criteria = {
                "lane": {
                    "assetType": "SHIPMENT",  # Search for loads
                    "equipment": {"types": [equipment_type]},
                    "origin": {
                        "place": {
                            "city": driver_location_city,
                            "stateProv": driver_location_state,
                            "latitude": coords["lat"],
                            "longitude": coords["lng"]
                        }
                    },
                    "destination": {"open": {}}
                },
                "maxAgeMinutes": 2880,  # 48 hours
                "maxOriginDeadheadMiles": filters.get("max_deadhead", 50) if filters else 50,
                "audience": {
                    "includeLoadBoard": True,
                    "includePrivateNetwork": True
                },
                "countsOnly": False
            }

            # Apply destination filter if provided
            if filters and filters.get("destination_state"):
                criteria["lane"]["destination"] = {
                    "area": {"states": [filters["destination_state"]]}
                }

            payload = {"criteria": criteria}

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }

            self.api_calls += 1
            print(f"📞 API Call #{self.api_calls}: Search Loads for Driver")
            print(f"📋 Searching from: {driver_location_city}, {driver_location_state}")

            response = self.session.post(
                f"{self.freight_url}/search/v3/queries",
                json=payload,
                headers=headers
            )

            if response.status_code != 201:
                print(f"❌ Load search failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

            data = response.json()
            query_id = data.get("queryId")

            if not query_id:
                print("❌ No query ID received")
                return None

            print(f"✅ Query created: {query_id}")

            # Get results
            self.api_calls += 1
            print(f"📞 API Call #{self.api_calls}: Get Load Results")

            match_response = self.session.get(
                f"{self.freight_url}/search/v3/queryMatches/{query_id}",
                headers=headers,
                params={"limit": limit}
            )

            if match_response.status_code != 200:
                print(f"❌ Failed to get load results: {match_response.status_code}")
                print(f"   Response: {match_response.text}")
                return None

            match_data = match_response.json()
            loads = match_data.get("matches", [])

            print(f"✅ Found {len(loads)} loads for driver")
            return loads

        except Exception as e:
            print(f"❌ Load search error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
