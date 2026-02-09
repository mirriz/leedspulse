from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String) # 'Crowding', 'Delay', 'Facilities' (List of options)
    severity = Column(Integer) # 1-5
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())