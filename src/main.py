from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel


import models, rail_service
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="RailPulse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class IncidentCreate(BaseModel):
    type: str
    severity: int
    description: Optional[str] = None

class IncidentUpdate(BaseModel):
    type: Optional[str] = None
    severity: Optional[int] = None
    description: Optional[str] = None

class IncidentResponse(IncidentCreate):
    id: uuid.UUID
    created_at: datetime
    class Config:
        from_attributes = True

class TrainResponse(BaseModel):
    from_code: str
    from_name: str
    origin_city: str
    scheduled: Optional[str] = None
    estimated: Optional[str] = None
    status: str
    delay_weight: int
    platform: Optional[str] = None
    delay_reason: Optional[str] = None




# --- ENDPOINTS ---
@app.get("/live/departures", response_model=List[TrainResponse], tags=["Live Departures"])
def get_live_departures():
    return rail_service.get_live_arrivals()

@app.post("/incidents", status_code=status.HTTP_201_CREATED, response_model=IncidentResponse, tags=["Incidents"])
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    new_incident = models.Incident(**incident.dict())
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    return new_incident

@app.put("/incidents/{incident_id}", response_model=IncidentResponse, tags=["Incidents"])
def update_incident(incident_id: uuid.UUID, update_data: IncidentUpdate, db: Session = Depends(get_db)):
    """
    [UPDATE] Modify an existing report (e.g. change Severity).
    """
    # Find report
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    
    # Check if exists
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Update the fields
    if update_data.type:
        incident.type = update_data.type
    if update_data.severity:
        incident.severity = update_data.severity
    if update_data.description:
        incident.description = update_data.description
    
    # Save changes
    db.commit()
    db.refresh(incident)
    return incident



@app.get("/incidents", response_model=List[IncidentResponse], tags=["Incidents"])
def get_incidents(db: Session = Depends(get_db)):
    return db.query(models.Incident).order_by(models.Incident.created_at.desc()).all()

@app.get("/analytics/hub-health", tags=["Analytics"])
def get_hub_health(db: Session = Depends(get_db)):
    rail_data = rail_service.get_live_arrivals()
    reports = db.query(models.Incident).all()
    
    total_severity = sum(r.severity for r in reports)
    delayed_trains = len([t for t in rail_data if t['status'] != 'On Time'])
    
    # Higher = Worse
    score = (total_severity * 2) + (delayed_trains * 5)
    
    color = "GREEN"
    if score > 50: color = "RED"
    elif score > 20: color = "AMBER"

    return {
        "timestamp": datetime.now(),
        "status": color,
        "score": score,
        "metrics": {
            "reports": len(reports),
            "delays": delayed_trains
        }
    }