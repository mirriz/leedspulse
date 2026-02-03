from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base


class Station(Base):
    __tablename__ = "stations"
    code = Column(String, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)

class Route(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True, index=True)
    origin_code = Column(String, ForeignKey("stations.code"))
    destination_code = Column(String, ForeignKey("stations.code"))
    label = Column(String)
    avg_travel_time_mins = Column(Integer)

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(Integer, ForeignKey("routes.id"))
    type = Column(String) # 'Crowding', 'Delay', 'Facilities' (List of options)
    severity = Column(Integer) # 1-5
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())