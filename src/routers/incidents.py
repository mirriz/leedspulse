from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from .. import models, schemas, database, auth

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.post("/", response_model=schemas.IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    incident: schemas.IncidentCreate, 
    # SECURE: Get user from token automatically
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
):
    # We don't need to check if user exists; auth.get_current_user does that.
    new_report = models.Incident(**incident.dict(), owner_id=current_user.id)
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

@router.get("/my-reports", response_model=List[schemas.IncidentResponse])
def get_my_incidents(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    return db.query(models.Incident).filter(models.Incident.owner_id == current_user.id).all()

@router.put("/{incident_id}", response_model=schemas.IncidentResponse)
def update_incident(
    incident_id: uuid.UUID, 
    update_data: schemas.IncidentUpdate, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # RBAC Check: Ensure the token owner owns the incident
    if incident.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if update_data.type: incident.type = update_data.type
    if update_data.severity: incident.severity = update_data.severity
    if update_data.description: incident.description = update_data.description
    
    db.commit()
    db.refresh(incident)
    return incident

@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(
    incident_id: uuid.UUID, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(incident)
    db.commit()
    return None