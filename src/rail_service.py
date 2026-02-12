import requests
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

BASE_URL = "https://huxley2.azurewebsites.net"
TOKEN = os.environ.get("OLDBWS_TOKEN")

def get_live_arrivals(hub_code="LDS"):
    # Use '/all' to get Arrivals AND Departures
    url = f"{BASE_URL}/all/{hub_code}/50?accessToken={TOKEN}&expand=true"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        trains = data.get("trainServices")
        if not trains:
            return []

        all_trains = []
        
        for train in trains:
            origin_list = train.get("origin", [])
            if origin_list:
                origin_crs = origin_list[0].get("crs")
                origin_name = origin_list[0].get("locationName")
            else:
                origin_crs = "UNK"
                origin_name = "Unknown Origin"
            

            sta = train.get("sta") 
            eta = train.get("eta")
            
            # If no arrival time, starts there
            if not sta:
                sta = train.get("std")
                eta = train.get("etd")
            
            # --- 3. DELAY CALCULATION ---
            status = "On Time"
            delay_minutes = 0
            
            if eta == "Cancelled":
                status = "Cancelled"
                delay_minutes = 60 # High penalty for analytics
            elif eta == "On time":
                status = "On Time"
                delay_minutes = 0
            elif eta and ":" in eta and sta and ":" in sta: 
                try:
                    # Parse HH:MM strings
                    t_sta = datetime.strptime(sta, "%H:%M")
                    t_eta = datetime.strptime(eta, "%H:%M")
                    
                    # Calculate difference in minutes
                    diff_mins = (t_eta - t_sta).total_seconds() / 60.0
                    
                    # Handle midnight edge case
                    if diff_mins < -720: 
                        diff_mins += 1440 
                    
                    delay_minutes = max(0, int(diff_mins))
                    
                    if delay_minutes > 0:
                        status = "Delayed"
                except (ValueError, TypeError):
                    # Fallback if time format is unexpected
                    delay_minutes = 0

            # --- 4. REFUND RADAR ---
            operator = train.get("operator", "")
            # 15 mins delay on major operators = Eligible
            refund_eligible = delay_minutes >= 15 and operator in ["Northern", "LNER", "TransPennine Express"]

            all_trains.append({
                "from_code": origin_crs,
                "from_name": origin_name,
                "origin_city": origin_name,
                "scheduled": sta,
                "estimated": eta,
                "status": status,
                "delay_weight": delay_minutes,
                "platform": train.get("platform"),
                "operator": operator,
                "refund_eligible": refund_eligible,
                "length": train.get("length", 0),
                "delay_reason": train.get("delayReason"),
                "train_id": train.get("serviceId")
            })
                
        return all_trains

    except Exception as e:
        print(f"API Error: {e}")
        # Fail gracefully with empty list (or mock data if you prefer)
        return []

if __name__ == "__main__":
    print("Scanning for all trains (Arrivals & Departures)...\n")
    results = get_live_arrivals()
    print(f"Found {len(results)} relevant trains.")
    for t in results:
        print(f" -> [{t['operator']}] {t['scheduled']} from {t['from_name']}: {t['status']} ({t['estimated']})")