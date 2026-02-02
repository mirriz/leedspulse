import os
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid


# Initialise the App
app = FastAPI(
    title="LeedsPulse API",
    description="Leeds Train Station Hub Analytics & Incident Reporting System",
    version="1.0.0"
)


class IncidentCreate(BaseModel):
    route_id: int
    type: str  # 'Crowding', 'Delay', 'Staff Issue', 'WiFi Problem', etc.
    severity: int  # 1-5
    description: Optional[str] = None

class IncidentResponse(IncidentCreate):
    id: uuid.UUID
    created_at: datetime




# The 5 Endpoints
@app.get("/live/departures", tags=["Utility"])
def get_live_departures():
    """
    Fetches departure data for Leeds (LDS) from the National Rail proxy.
    """
    return {"message": "Coming soon: Live Huxley Data Integration"}


@app.post("/incidents", status_code=status.HTTP_201_CREATED, tags=["CRUD Operations"])
def create_incident(incident: IncidentCreate):
    """
    Submit a new passenger report.
    Required: route_id, type, severity (1-5).
    """
    # TODO: Connect to Database
    return {"status": "success", "message": "Incident reported", "data": incident}


@app.get("/incidents", response_model=List[IncidentResponse], tags=["CRUD Operations"])
def get_incidents():
    """
    Get all recent incidents for the Leeds network.
    """
    # TODO: Connect to Database
    return []


@app.delete("/incidents/{incident_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["CRUD Operations"])
def delete_incident(incident_id: uuid.UUID):
    """
    Remove a passenger report by ID.
    """
    # TODO: Connect to Database
    return None


@app.get("/analytics/hub-health", tags=["Innovation"])
def get_hub_health():
    """
    Calculates the real-time Health Score of Leeds Station.
    Combines official delays with passenger severity reports.
    """
    return {
        "hub_status": "CALCULATING...",
        "spokes": {
            "Manchester Piccadilly": "UNKNOWN",
            "York": "UNKNOWN",
            "Harrogate": "UNKNOWN",
            "Wakefield Westgate": "UNKNOWN"
        }
    }


