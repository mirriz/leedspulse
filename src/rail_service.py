import requests

BASE_URL = "https://huxley2.azurewebsites.net"

# The 4 critical inbound lines to monitor
SPOKES = {
    "MAN": "Manchester Piccadilly",
    "YRK": "York",
    "WKF": "Wakefield Westgate",
    "HGT": "Harrogate"
}

def get_live_arrivals(hub_code="LDS"):
    try:
        response = requests.get(f"{BASE_URL}/arrivals/{hub_code}/20")
        response.raise_for_status()
        data = response.json()
        
        trains = data.get("trainServices")
        if not trains:
            return []

        relevant_trains = []
        
        for train in trains:
            origin_list = train.get("origin", [])
            if not origin_list:
                continue
            
            origin_crs = origin_list[0].get("crs")
            
            # Handle pass-through trains (e.g., London -> Wakefield -> Leeds)
            prev_points_data = train.get("previousCallingPoints", [])
            calling_points = prev_points_data[0].get("callingPoint", []) if prev_points_data else []
            
            matched_spoke = None
            
            # Is the origin itself a spoke?
            if origin_crs in SPOKES:
                matched_spoke = origin_crs
            # Did it stop at a spoke on the way?
            else:
                for point in calling_points:
                    if point.get("crs") in SPOKES:
                        matched_spoke = point.get("crs")
                        # Don't break; finds the closest spoke if multiple exist
            
            if matched_spoke:
                et = train.get("et")
                std = train.get("std")
                
                delay_minutes = 0
                status = "On Time"
                
                if et == "Cancelled":
                    status = "Cancelled"
                    delay_minutes = 60
                    
                elif et and et != "On time":
                    status = "Delayed"
                    # Placeholder delay weight 
                    delay_minutes = 10 
                
                relevant_trains.append({
                    "from_code": matched_spoke,
                    "from_name": SPOKES[matched_spoke],
                    "origin_city": origin_list[0].get("locationName"),
                    "scheduled": std,
                    "estimated": et,
                    "status": status,
                    "delay_weight": delay_minutes,
                    "platform": train.get("platform", "TBC")
                })
                
        return relevant_trains

    except Exception as e:
        print(f"Error fetching rail data: {e}. MOCK DATA MODE.")

        return [
        {
            "from_code": "MAN",
            "from_name": "Manchester Piccadilly",
            "origin_city": "Manchester Piccadilly",
            "scheduled": "18:00",
            "estimated": "18:25",
            "status": "Delayed",
            "delay_weight": 25,
            "platform": "12"
        },
        {
            "from_code": "YRK",
            "from_name": "York",
            "origin_city": "York",
            "scheduled": "18:05",
            "estimated": "On time",
            "status": "On Time",
            "delay_weight": 0,
            "platform": "5"
        },
        {
            "from_code": "WKF", 
            "from_name": "Wakefield Westgate",
            "origin_city": "London Kings Cross", 
            "scheduled": "18:10",
            "estimated": "Cancelled",
            "status": "Cancelled",
            "delay_weight": 60,
            "platform": "TBC"
        },
        {
            "from_code": "HGT",
            "from_name": "Harrogate",
            "origin_city": "Harrogate",
            "scheduled": "18:20",
            "estimated": "On time",
            "status": "On Time",
            "delay_weight": 0,
            "platform": "1"
        }
    ]

if __name__ == "__main__":
    results = get_live_arrivals()
    print(f"Found {len(results)} relevant trains.")
    for t in results:
        print(f" -> From {t['from_name']} (Started: {t['origin_city']}): {t['status']} - {t['estimated']}")