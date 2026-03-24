from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=True)

    patient_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    surgery_type = Column(String, nullable=False)
    surgery_side = Column(String, nullable=False)
    surgery_date = Column(Date, nullable=True)

    role = Column(String, nullable=False, default="patient")
    created_at = Column(DateTime, default=datetime.utcnow)

    # gait_records = relationship(
    #     "GaitRecord",
    #     back_populates="user",
    #     cascade="all, delete-orphan"
    # )


class GaitRecord(Base):
    __tablename__ = "gait_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    record_date = Column(Date, nullable=False, index=True)
    step_count = Column(Integer, nullable=False)
    walking_speed = Column(Float, nullable=True)
    cadence = Column(Float, nullable=True)
    distance = Column(Float, nullable=True)
    active_minutes = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # user = relationship("User", back_populates="gait_records")