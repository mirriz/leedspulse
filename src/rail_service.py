import requests
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = "https://huxley2.azurewebsites.net"
TOKEN = os.environ.get("OLDBWS_TOKEN")

def get_live_arrivals(hub_code="LDS"):
    url = f"{BASE_URL}/arrivals/{hub_code}/20?accessToken={TOKEN}&expand=true"
    
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
            if not origin_list:
                continue
                
            origin_data = origin_list[0]
            origin_crs = origin_data.get("crs")
            origin_name = origin_data.get("locationName")
            
            sta = train.get("sta")
            eta = train.get("eta")
            
            status = "On Time"
            delay_minutes = 0
            
            if eta == "Cancelled":
                status = "Cancelled"
                delay_minutes = 60
            elif eta == "On time":
                status = "On Time"
            elif eta and eta != "On time":
                status = "Delayed"
                delay_minutes = 10 
            
            all_trains.append({
                "from_code": origin_crs,
                "from_name": origin_name,
                "origin_city": origin_name,
                "scheduled": sta,
                "estimated": eta,
                "status": status,
                "delay_weight": delay_minutes,
                "platform": train.get("platform"),
                "operator": train.get("operator"),
                "length": train.get("length", 0),
                "delay_reason": train.get("delayReason")
            })
                
        return all_trains

    except Exception as e:
        print(f"API Error: {e}")
        return [
        {
            "from_code": "MAN",
            "from_name": "Manchester Piccadilly",
            "origin_city": "Manchester Piccadilly",
            "scheduled": "18:00",
            "estimated": "18:15", # Late!
            "status": "Delayed",
            "delay_weight": 15,
            "platform": "12",
            "delay_reason": "Signal failure at Leeds"
        },
        {
            "from_code": "YRK",
            "from_name": "York",
            "origin_city": "York",
            "scheduled": "18:05",
            "estimated": "On time",
            "status": "On Time",
            "delay_weight": 0,
            "platform": "8",
            "delay_reason": None
        },
        {
            "from_code": "WKF",
            "from_name": "Wakefield Westgate",
            "origin_city": "London Kings Cross",
            "scheduled": "18:10",
            "estimated": "Cancelled", # Severe!
            "status": "Cancelled",
            "delay_weight": 60,
            "platform": "TBC",
            "delay_reason": "Train cancelled due to staff shortage"
        },
         {
            "from_code": "HGT",
            "from_name": "Harrogate",
            "origin_city": "Harrogate",
            "scheduled": "18:20",
            "estimated": "On time",
            "status": "On Time",
            "delay_weight": 0,
            "platform": "1",
            "delay_reason": None
        }
    ]

if __name__ == "__main__":

    print("Scanning for trains (Direct & Pass-Through)...\n")
    results = get_live_arrivals()
        
    print(f"Found {len(results)} relevant trains.")
    for t in results:
        print(f" -> [Line: {t['from_code']}] {t['scheduled']} Service from {t['origin_city']}: {t['status']}. {t['delay_reason'] if t['delay_reason'] else ''} ({t['estimated']}). Platform {t['platform'] if t['platform'] else 'TBC'}")