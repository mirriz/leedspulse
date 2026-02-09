from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError 


import models, rail_service
from database import engine, get_db
from auth import get_password_hash, verify_password

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="LeedsPulse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    class Config:
        from_attributes = True

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
def create_incident(
    incident: IncidentCreate, 
    user_id: uuid.UUID,  # Now Required
    db: Session = Depends(get_db)
):
    # Verify user exists
    get_user_or_404(user_id, db)

    new_incident = models.Incident(
        owner_id=user_id, # Link to the user
        train_id=incident.train_id,
        type=incident.type,
        severity=incident.severity,
        description=incident.description
    )
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    return new_incident



@app.put("/incidents/{incident_id}", response_model=IncidentResponse, tags=["Incidents"])
def update_incident(
    incident_id: uuid.UUID, 
    user_id: uuid.UUID, # We need to know WHO is asking
    update_data: IncidentUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update a report. Fails if the user is not the owner.
    """
    # 1. Find the report
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    
    # Check existence
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    #Check Ownership
    if incident.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this report")
    
    # Update fields
    if update_data.type: incident.type = update_data.type
    if update_data.severity: incident.severity = update_data.severity
    if update_data.description: incident.description = update_data.description
    
    db.commit()
    db.refresh(incident)
    return incident



@app.get("/incidents/my-reports", response_model=List[IncidentResponse], tags=["Incidents"])
def get_my_incidents(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Fetch reports created by the user.
    """
    # Verify user exists
    get_user_or_404(user_id, db)
    
    # Filter by owner_id
    reports = db.query(models.Incident).filter(models.Incident.owner_id == user_id).all()
    return reports



@app.delete("/incidents/{incident_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Incidents"])
def delete_incident(
    incident_id: uuid.UUID, 
    user_id: uuid.UUID, 
    db: Session = Depends(get_db)
):
    """
    [SECURE] Delete a report. Fails if the user is not the owner.
    """
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if incident.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this report")
    
    db.delete(incident)
    db.commit()
    return None



# ANALYTICS
@app.get("/analytics/leeds-health", tags=["Analytics"])
def get_hub_health(db: Session = Depends(get_db)):
    """
    Combines live rail data with user-reported incidents to give an overall health score for Leeds.
     - More severe incidents and more delays = worse score
     - Score is translated into a simple status (Green/Amber/Red)
    """
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






# ACCOUNT CREATION
@app.post("/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user. Hashes the password before saving.
    """
    # Check if email already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_pwd = get_password_hash(user.password)

    # Save to DB
    new_user = models.User(email=user.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.put("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def update_user(user_id: uuid.UUID, user_update: UserUpdate, db: Session = Depends(get_db)):
    """
    Update email or password.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update Email (if provided)
    if user_update.email:
        # Check for duplicates
        duplicate_check = db.query(models.User).filter(models.User.email == user_update.email).first()
        if duplicate_check and duplicate_check.id != user_id:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = user_update.email

    # Update Password
    if user_update.password:
        user.hashed_password = get_password_hash(user_update.password)

    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a user. 
    This cascades and deletes all their reports too (GDPR).
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return None


@app.post("/users/login", tags=["Users"])
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Checks email and password. Returns User ID if valid.
    Use POST so credentials are not visible in the URL.
    """
    # Find the user by email
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    
    # Check if user exists AND if password matches has      h
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password"
        )
    
    # Return the user ID
    return {
        "message": "Login successful", 
        "user_id": user.id,
        "email": user.email
    }



def get_user_or_404(user_id: uuid.UUID, db: Session):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user