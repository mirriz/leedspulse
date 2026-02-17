import requests
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

BASE_URL = "https://huxley2.azurewebsites.net"
TOKEN = os.environ.get("OLDBWS_TOKEN")

def get_live_arrivals(hub_code="LDS"):
    # Using /all/ to capture both Arrivals and Departures
    url = f"{BASE_URL}/all/{hub_code}/50?accessToken={TOKEN}&expand=true"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # 1. CAPTURE THE FULL STATION NAME
        station_name = data.get("locationName", hub_code) 
        
        trains = data.get("trainServices")
        if not trains:
            return {"station_name": station_name, "trains": []}

        all_trains = []
        
        for train in trains:
            # Safe Origin Parsing
            origin_list = train.get("origin", [])
            if origin_list:
                origin_crs = origin_list[0].get("crs")
                origin_name = origin_list[0].get("locationName")
            else:
                origin_crs = "UNK"
                origin_name = "Unknown Origin"
            
            # Time Parsing (Arrivals vs Starts)
            sta = train.get("sta") 
            eta = train.get("eta")
            
            if not sta:
                sta = train.get("std")
                eta = train.get("etd")
            
            status = "On Time"
            delay_minutes = 0
            
            # Delay Logic
            if eta == "Cancelled":
                status = "Cancelled"
                delay_minutes = 60 
            elif eta == "On time":
                status = "On Time"
                delay_minutes = 0
            elif eta and ":" in eta and sta and ":" in sta: 
                try:
                    t_sta = datetime.strptime(sta, "%H:%M")
                    t_eta = datetime.strptime(eta, "%H:%M")
                    diff_mins = (t_eta - t_sta).total_seconds() / 60.0
                    
                    if diff_mins < -720: diff_mins += 1440
                    
                    delay_minutes = max(0, int(diff_mins))
                    if delay_minutes > 0: status = "Delayed"
                except (ValueError, TypeError):
                    delay_minutes = 0

            # Refund Logic
            operator = train.get("operator", "")
            refund_eligible = delay_minutes >= 15

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
                
        # 2. RETURN DICTIONARY (Fixes your error)
        return {
            "station_name": station_name,
            "trains": all_trains
        }

    except Exception as e:
        return {"station_name": "Unknown", "trains": []}

if __name__ == "__main__":
    print("Scanning for all trains (Arrivals & Departures)...\n")
    results = get_live_arrivals()
    print(f"Found {len(results['trains'])} relevant trains.")
    for t in results['trains']:
        print(f" -> [{t['operator']}] {t['scheduled']} from {t['from_name']}: {t['status']} ({t['estimated']})")