from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    DateTime,
    Date,
    ForeignKey,
    Float,
    UniqueConstraint,
    Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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

    gait_records = relationship(
        "GaitRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    patient_reports = relationship(
        "PatientReport",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class GaitRecord(Base):
    __tablename__ = "gait_records"
    __table_args__ = (
        UniqueConstraint("user_id", "record_date", name="uq_user_record_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    record_date = Column(Date, nullable=False, index=True)
    step_count = Column(Integer, nullable=False)
    walking_speed = Column(Float, nullable=True)
    cadence = Column(Float, nullable=True)
    distance = Column(Float, nullable=True)
    active_minutes = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="gait_records")


class PatientReport(Base):
    __tablename__ = "patient_reports"
    __table_args__ = (
        UniqueConstraint("user_id", "report_date", name="uq_user_report_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    report_date = Column(Date, nullable=False, index=True)
    pain_score = Column(Integer, nullable=False)
    stiffness_score = Column(Integer, nullable=False)
    walking_difficulty = Column(Integer, nullable=False)
    confidence_score = Column(Integer, nullable=False)
    swelling_flag = Column(Boolean, default=False, nullable=False)
    exercise_completed = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="patient_reports")