from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


class UserRegister(BaseModel):
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date | None = None

    patient_id: str
    email: EmailStr
    password: str

    surgery_type: str
    surgery_side: str
    surgery_date: date | None = None


class UserCreateByAdmin(BaseModel):
    patient_id: str
    email: EmailStr
    password: str
    surgery_type: str
    surgery_side: str
    role: str  # patient / clinician / admin


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date | None = None

    patient_id: str
    email: EmailStr

    surgery_type: str
    surgery_side: str
    surgery_date: date | None = None

    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class GaitRecordCreate(BaseModel):
    record_date: date
    step_count: int
    walking_speed: Optional[float] = None
    cadence: Optional[float] = None
    distance: Optional[float] = None
    active_minutes: Optional[int] = None


class GaitRecordOut(BaseModel):
    id: int
    user_id: int
    record_date: date
    step_count: int
    walking_speed: Optional[float] = None
    cadence: Optional[float] = None
    distance: Optional[float] = None
    active_minutes: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientDashboard(BaseModel):
    patient_id: str
    surgery_type: str
    surgery_side: str
    total_records: int
    latest_record: Optional[GaitRecordOut] = None
    average_step_count: float
    average_walking_speed: Optional[float] = None
    average_cadence: Optional[float] = None


class ClinicianPatientSummary(BaseModel):
    patient_id: str
    email: EmailStr
    surgery_type: str
    surgery_side: str
    total_records: int


class ClinicianDashboard(BaseModel):
    total_patients: int
    total_gait_records: int
    patients: List[ClinicianPatientSummary]