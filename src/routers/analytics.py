from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from .. import models, schemas, database, rail_service

router = APIRouter(tags=["Analytics"])

@router.get("/live/departures/{station_code}", response_model=List[schemas.TrainResponse])
def get_live_departures(station_code: str):
    # Fetch the full data
    data = rail_service.get_live_arrivals(hub_code=station_code)
    # Return the list of trains
    return data.get("trains", [])

@router.get("/analytics/{station_code}/health")
def get_hub_health(station_code: str, db: Session = Depends(database.get_db)):
    # Fetch Data 
    service_response = rail_service.get_live_arrivals(hub_code=station_code)
    
    # Get data with defaults
    rail_data = service_response.get("trains", [])       
    full_station_name = service_response.get("station_name", "Unknown Station")

    # Fetch User Reports
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_reports = db.query(models.Incident).filter(
        models.Incident.created_at >= one_hour_ago,
        models.Incident.station_code == station_code 
    ).all()

    # Calculate Rail Metrics
    cancelled_trains = len([t for t in rail_data if t['status'] == 'Cancelled'])
    
    active_trains = [t for t in rail_data if t['status'] != 'Cancelled']
    avg_delay = 0
    if active_trains:
        avg_delay = sum(t['delay_weight'] for t in active_trains) / len(active_trains)

    # Crowd Metrics
    avg_severity = 0
    if recent_reports:
        avg_severity = sum(r.severity for r in recent_reports) / len(recent_reports)

    # Score Algorithm (0.0 - 1.0)
    score = (avg_severity / 5.0 * 0.4) + (min(avg_delay, 60) / 60.0 * 0.6)
    
    # Determine Status Band
    status = "GREEN"
    if score > 0.7: status = "RED"
    elif score > 0.35: status = "AMBER"
    
    # Domain Override
    if cancelled_trains > (len(rail_data) * 0.25): 
        status = "Amber"
        score = max(score, 0.35)
    elif cancelled_trains > (len(rail_data) * 0.5):
        status = "Red"
        score = max(score, 0.7)
    

    return {
        "station": full_station_name, 
        "station_code": station_code,
        "timestamp": datetime.now(),
        "hub_status": status,
        "stress_index": round(score, 2),
        "metrics": {
            "cancellations": cancelled_trains,
            "avg_delay": round(avg_delay, 1),
            "passenger_reports": len(recent_reports),
            "avg_report_severity": round(avg_severity, 1)
        }
    }