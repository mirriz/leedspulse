from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from .. import models, schemas, database, rail_service

router = APIRouter(tags=["Analytics"])

@router.get("/live/departures", response_model=List[schemas.TrainResponse])
def get_live_departures():
    return rail_service.get_live_arrivals()

@router.get("/analytics/hub-health")
def get_hub_health(db: Session = Depends(database.get_db)):
    # 1. Logic: Last 1 Hour
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    rail_data = rail_service.get_live_arrivals()
    recent_reports = db.query(models.Incident).filter(
        models.Incident.created_at >= one_hour_ago
    ).all()
    
    # 2. Metrics
    cancelled_trains = len([t for t in rail_data if t['status'] == 'Cancelled'])
    
    active_trains = [t for t in rail_data if t['status'] != 'Cancelled']
    avg_delay = 0
    if active_trains:
        avg_delay = sum(t['delay_weight'] for t in active_trains) / len(active_trains)

    avg_severity = 0
    if recent_reports:
        avg_severity = sum(r.severity for r in recent_reports) / len(recent_reports)

    # 3. Score (0.0 - 1.0)
    score = (avg_severity/5.0 * 0.4) + (min(avg_delay, 60)/60.0 * 0.6)
    
    status = "GREEN"
    if score > 0.7: status = "RED"
    elif score > 0.35: status = "AMBER"
    
    # Domain Knowledge Override
    if cancelled_trains > 3: status = "RED"

    return {
        "timestamp": datetime.now(),
        "hub_status": status,
        "stress_index": round(score, 2),
        "metrics": {
            "cancellations": cancelled_trains,
            "avg_delay": round(avg_delay, 1),
            "reports_last_hour": len(recent_reports)
        }
    }