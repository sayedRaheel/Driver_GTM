#!/usr/bin/env python3
"""
Driver GTM - efRouting Scoring Module
Simplified scoring logic adapted from TopLoads for driver-load matching
"""

from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

# Scoring weights (from TopLoads config)
SCORING_WEIGHTS = {
    'profit': 0.50,
    'connectivity': 0.30,
    'ease': 0.20
}

# Operational costs
FUEL_PRICE_DEFAULT = 3.89  # $/gallon
FUEL_EFFICIENCY = {
    'V': 6.6,   # Van MPG
    'R': 6.0,   # Reefer MPG
    'F': 5.8    # Flatbed MPG
}
OPS_COST_PER_MILE = 0.40  # Non-fuel operational costs


def calculate_load_profit(load: Dict, origin_state: str = "TX") -> Dict:
    """
    Calculate profit potential for a load

    Args:
        load: Load data from DAT API
        origin_state: Origin state (for future fuel price lookups)

    Returns:
        Dict with profit data and score (0-100)
    """
    asset_info = load.get("matchingAssetInfo", {})

    # Get trip details
    trip_miles = load.get("tripLength", {}).get("miles", 0)

    # Get deadhead miles
    origin_deadhead = 0
    dh = (load.get("originDeadhead") or {}).get("miles")
    if dh is None:
        dh = (load.get("originDeadheadMiles") or {}).get("miles", 0)
    origin_deadhead = dh or 0

    total_miles = trip_miles + origin_deadhead

    # Extract rate per mile (prioritize estimatedRatePerMile)
    rate_per_mile = 0

    if load.get("estimatedRatePerMile"):
        rate_per_mile = load["estimatedRatePerMile"]
    elif load.get("loadBoardRateInfo"):
        load_board_rate_info = load["loadBoardRateInfo"]
        rate_info = load_board_rate_info.get("nonBookable", {}) or load_board_rate_info.get("bookable", {})
        if rate_info.get("rateUsd") and rate_info.get("basis") == "FLAT":
            rate_per_mile = rate_info["rateUsd"] / max(trip_miles, 1) if trip_miles > 0 else 0
        elif rate_info.get("rateUsd") and rate_info.get("basis") == "PER_MILE":
            rate_per_mile = rate_info["rateUsd"]

    # Fallback rates if no rate found
    if rate_per_mile == 0:
        equipment = asset_info.get("equipmentType", "V")
        if equipment == "R":
            rate_per_mile = 2.60 if trip_miles > 500 else 2.90
        else:
            rate_per_mile = 2.30 if trip_miles > 500 else 2.70

    total_revenue = rate_per_mile * trip_miles

    # Calculate costs
    equipment = asset_info.get("equipmentType", "V")
    fuel_efficiency = FUEL_EFFICIENCY.get(equipment, 6.6)
    fuel_cost = (total_miles / fuel_efficiency) * FUEL_PRICE_DEFAULT
    ops_cost = total_miles * OPS_COST_PER_MILE
    total_costs = fuel_cost + ops_cost

    net_profit = total_revenue - total_costs
    profit_per_mile = net_profit / max(total_miles, 1)

    # Score profit (0-100 scale)
    if profit_per_mile >= 1.50:
        profit_score = 95
    elif profit_per_mile >= 1.00:
        profit_score = 85
    elif profit_per_mile >= 0.75:
        profit_score = 70
    elif profit_per_mile >= 0.50:
        profit_score = 55
    elif profit_per_mile >= 0.25:
        profit_score = 40
    elif profit_per_mile >= 0:
        profit_score = 25
    else:
        profit_score = 10

    return {
        "total_revenue": round(total_revenue, 2),
        "fuel_cost": round(fuel_cost, 2),
        "ops_cost": round(ops_cost, 2),
        "total_costs": round(total_costs, 2),
        "net_profit": round(net_profit, 2),
        "profit_per_mile": round(profit_per_mile, 2),
        "total_miles": total_miles,
        "trip_miles": trip_miles,
        "origin_deadhead": origin_deadhead,
        "rate_per_mile": round(rate_per_mile, 2),
        "equipment_type": equipment,
        "score": profit_score
    }


def get_market_data(state: str, equipment_types: List[str], dat_client) -> Dict:
    """
    Get market analysis for a destination state

    Args:
        state: Destination state code
        equipment_types: List of equipment types
        dat_client: DATClient instance for API calls

    Returns:
        Market data with ease and connectivity scores
    """
    if not dat_client.access_token:
        return {
            "state": state,
            "outbound_loads": 0,
            "available_trucks": 0,
            "supply_demand_ratio": 0,
            "ease_of_booking": {"score": 0, "rating": "Unknown"},
            "lane_connectivity": {"score": 0, "rating": "Unknown"}
        }

    try:
        import requests
        import json

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {dat_client.access_token}"
        }

        # Get outbound loads FROM this state
        outbound_payload = {
            "criteria": {
                "lane": {
                    "assetType": "SHIPMENT",
                    "equipment": {"types": equipment_types},
                    "origin": {"area": {"states": [state]}},
                    "destination": {"open": {}}
                },
                "maxAgeMinutes": 2880,
                "audience": {
                    "includeLoadBoard": True,
                    "includePrivateNetwork": True
                },
                "countsOnly": False
            }
        }

        # Get trucks available IN this state
        trucks_payload = {
            "criteria": {
                "lane": {
                    "assetType": "TRUCK",
                    "equipment": {"types": equipment_types},
                    "origin": {"area": {"states": [state]}},
                    "destination": {"open": {}}
                },
                "maxAgeMinutes": 2880,
                "audience": {
                    "includeLoadBoard": True,
                    "includePrivateNetwork": True
                },
                "countsOnly": False,
                "includeOpenDestinationTrucks": True
            }
        }

        outbound_count = 0
        trucks_count = 0

        # Query outbound loads
        response = dat_client.session.post(
            f"{dat_client.freight_url}/search/v3/queries",
            headers=headers,
            data=json.dumps(outbound_payload)
        )

        if response.status_code in (200, 201):
            data = response.json()
            query_id = data.get("queryId")

            if query_id:
                count_response = dat_client.session.get(
                    f"{dat_client.freight_url}/search/v3/queryMatches/{query_id}",
                    headers=headers,
                    params={"staticView": "JUST_COUNTS", "limit": 1}
                )

                if count_response.status_code == 200:
                    count_data = count_response.json()
                    match_counts = count_data.get("matchCounts", {})
                    outbound_count = (
                        match_counts.get("normal", 0) +
                        match_counts.get("preferred", 0) +
                        match_counts.get("privateNetwork", 0)
                    )

        # Query trucks
        truck_response = dat_client.session.post(
            f"{dat_client.freight_url}/search/v3/queries",
            headers=headers,
            data=json.dumps(trucks_payload)
        )

        if truck_response.status_code in (200, 201):
            truck_data = truck_response.json()
            truck_query_id = truck_data.get("queryId")

            if truck_query_id:
                truck_count_response = dat_client.session.get(
                    f"{dat_client.freight_url}/search/v3/queryMatches/{truck_query_id}",
                    headers=headers,
                    params={"staticView": "JUST_COUNTS", "limit": 1}
                )

                if truck_count_response.status_code == 200:
                    truck_count_data = truck_count_response.json()
                    truck_match_counts = truck_count_data.get("matchCounts", {})
                    trucks_count = (
                        truck_match_counts.get("normal", 0) +
                        truck_match_counts.get("preferred", 0) +
                        truck_match_counts.get("privateNetwork", 0)
                    )

        # Calculate metrics
        sdr = trucks_count / max(outbound_count, 1)

        # Ease of Booking score
        if outbound_count == 0 and trucks_count == 0:
            ease_score = 0
            ease_rating = "No Market"
        elif sdr <= 0.5:
            ease_score = 95
            ease_rating = "Excellent"
        elif sdr <= 1.0:
            ease_score = 85
            ease_rating = "Excellent"
        elif sdr <= 1.5:
            ease_score = 70
            ease_rating = "Balanced"
        elif sdr <= 2.5:
            ease_score = 50
            ease_rating = "Balanced"
        elif sdr <= 4.0:
            ease_score = 35
            ease_rating = "Difficult"
        else:
            ease_score = 20
            ease_rating = "Difficult"

        # Lane Connectivity score
        if outbound_count >= 100:
            connectivity_score = 90
            connectivity_rating = "High"
        elif outbound_count >= 50:
            connectivity_score = 70
            connectivity_rating = "Medium"
        elif outbound_count >= 20:
            connectivity_score = 50
            connectivity_rating = "Low"
        else:
            connectivity_score = 20
            connectivity_rating = "Very Low"

        print(f"   📊 {state}: {outbound_count} loads, {trucks_count} trucks, SDR: {sdr:.2f}, Ease: {ease_score}, Connectivity: {connectivity_score}")

        return {
            "state": state,
            "outbound_loads": outbound_count,
            "available_trucks": trucks_count,
            "supply_demand_ratio": round(sdr, 2),
            "ease_of_booking": {
                "score": ease_score,
                "rating": ease_rating
            },
            "lane_connectivity": {
                "score": connectivity_score,
                "rating": connectivity_rating
            }
        }

    except Exception as e:
        print(f"❌ Market analysis error for {state}: {str(e)}")
        return {
            "state": state,
            "outbound_loads": 0,
            "available_trucks": 0,
            "supply_demand_ratio": 0,
            "ease_of_booking": {"score": 0, "rating": "Error"},
            "lane_connectivity": {"score": 0, "rating": "Error"}
        }


def calculate_composite_score(profit_data: Dict, market_data: Dict) -> Dict:
    """
    Calculate final composite score using efRouting methodology

    Args:
        profit_data: Profit calculation results
        market_data: Market analysis results

    Returns:
        Composite score and recommendation
    """
    profit_score = profit_data.get("score", 0)
    connectivity_score = market_data.get("lane_connectivity", {}).get("score", 0)
    ease_score = market_data.get("ease_of_booking", {}).get("score", 0)

    composite_score = (
        profit_score * SCORING_WEIGHTS['profit'] +
        connectivity_score * SCORING_WEIGHTS['connectivity'] +
        ease_score * SCORING_WEIGHTS['ease']
    )

    # Recommendation based on score
    if composite_score >= 80:
        recommendation = "Highly Recommended"
        color = "green"
    elif composite_score >= 60:
        recommendation = "Recommended"
        color = "yellow"
    elif composite_score >= 40:
        recommendation = "Consider"
        color = "orange"
    else:
        recommendation = "Avoid"
        color = "red"

    return {
        "composite_score": round(composite_score, 1),
        "recommendation": recommendation,
        "color": color,
        "individual_scores": {
            "profit": profit_score,
            "connectivity": connectivity_score,
            "ease": ease_score
        }
    }


def extract_unique_destination_states(loads: List[Dict]) -> Set[str]:
    """Extract unique destination states from loads"""
    unique_states = set()

    for load in loads:
        asset_info = load.get("matchingAssetInfo", {})
        destination = asset_info.get("destination", {})

        # Handle destination.place.stateProv
        place = destination.get("place", {})
        if place.get("stateProv"):
            unique_states.add(place["stateProv"])

        # Handle destination.area.states
        area = destination.get("area", {})
        if area.get("states"):
            unique_states.update(area["states"])

    return unique_states


def analyze_loads_for_driver(loads: List[Dict], driver_location_state: str, dat_client) -> List[Dict]:
    """
    Analyze loads using efRouting scoring

    Args:
        loads: List of loads from DAT API
        driver_location_state: Driver's current state
        dat_client: DATClient instance for market analysis

    Returns:
        List of analyzed and scored loads
    """
    if not loads:
        return []

    print(f"\n📊 Analyzing {len(loads)} loads for driver using efRouting...")

    # Extract unique destination states
    all_destinations = extract_unique_destination_states(loads)

    # Limit to top 5-10 destinations for API efficiency (Option C - Hybrid approach)
    unique_destinations = list(all_destinations)[:10]

    print(f"🎯 Found {len(all_destinations)} unique destinations, analyzing top {len(unique_destinations)}")

    # Get market data for each destination in parallel
    market_data_cache = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_state = {
            executor.submit(get_market_data, state, ["V", "R", "F"], dat_client): state
            for state in unique_destinations
        }

        for future in as_completed(future_to_state):
            state = future_to_state[future]
            try:
                market_data_cache[state] = future.result()
            except Exception as exc:
                print(f"   ❌ {state} analysis failed: {exc}")
                market_data_cache[state] = {
                    "state": state,
                    "outbound_loads": 0,
                    "available_trucks": 0,
                    "supply_demand_ratio": 0,
                    "ease_of_booking": {"score": 0, "rating": "Error"},
                    "lane_connectivity": {"score": 0, "rating": "Error"}
                }

    # Analyze each load
    analyzed_loads = []

    for i, load in enumerate(loads, 1):
        asset_info = load.get("matchingAssetInfo", {})
        destination = asset_info.get("destination", {})

        # Get destination state
        dest_state = None
        place = destination.get("place", {})
        if place.get("stateProv"):
            dest_state = place["stateProv"]
        else:
            area = destination.get("area", {})
            if area.get("states"):
                dest_state = list(area["states"])[0]

        if not dest_state:
            continue

        # Calculate profit
        profit_data = calculate_load_profit(load, driver_location_state)

        # Get market data from cache
        market_data = market_data_cache.get(dest_state, {})

        # Calculate composite score
        composite_data = calculate_composite_score(profit_data, market_data)

        # Extract origin/destination info
        origin = asset_info.get("origin", {})

        analyzed_load = {
            "load_number": i,
            "match_id": load.get("matchId", ""),
            "origin": {
                "city": origin.get("city", ""),
                "state": origin.get("stateProv", "")
            },
            "destination": {
                "city": place.get("city", ""),
                "state": dest_state
            },
            "profit_data": profit_data,
            "market_data": market_data,
            "composite_data": composite_data,
            "raw_load": load  # Keep raw load data for frontend display
        }

        analyzed_loads.append(analyzed_load)

    # Sort by composite score
    analyzed_loads.sort(key=lambda x: x["composite_data"]["composite_score"], reverse=True)

    print(f"✅ Analyzed {len(analyzed_loads)} loads, sorted by efRouting score")

    return analyzed_loads
