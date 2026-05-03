from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict, Field


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

class PatientReportCreate(BaseModel):
    report_date: date
    pain_score: int = Field(..., ge=0, le=10)
    stiffness_score: int = Field(..., ge=0, le=10)
    walking_difficulty: int = Field(..., ge=0, le=10)
    confidence_score: int = Field(..., ge=0, le=10)
    swelling_flag: bool = False
    exercise_completed: bool = False
    notes: Optional[str] = None


class PatientReportOut(BaseModel):
    id: int
    user_id: int
    report_date: date
    pain_score: int
    stiffness_score: int
    walking_difficulty: int
    confidence_score: int
    swelling_flag: bool
    exercise_completed: bool
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PatientReportSummaryOut(PatientReportOut):
    recovery_score: int
    recovery_status: str
    recovery_message: str


# ---------------------------------------------------------------------------
# Admin / clinician dashboard schemas
# ---------------------------------------------------------------------------


class PatientTableRow(BaseModel):
    id: int
    patient_id: str
    first_name: str
    last_name: str
    email: EmailStr
    gender: str
    date_of_birth: date | None = None
    surgery_type: str
    surgery_side: str
    surgery_date: date | None = None
    days_since_surgery: Optional[int] = None
    total_gait_records: int
    total_reports: int
    last_gait_date: Optional[date] = None
    last_report_date: Optional[date] = None
    latest_recovery_score: Optional[int] = None
    latest_recovery_status: Optional[str] = None


class GaitSeriesPoint(BaseModel):
    record_date: date
    step_count: int
    walking_speed: Optional[float] = None
    cadence: Optional[float] = None
    distance: Optional[float] = None
    active_minutes: Optional[int] = None


class ReportSeriesPoint(BaseModel):
    report_date: date
    pain_score: int
    stiffness_score: int
    walking_difficulty: int
    confidence_score: int
    swelling_flag: bool
    exercise_completed: bool
    recovery_score: int
    recovery_status: str


class PatientDetailOut(BaseModel):
    profile: PatientTableRow
    recent_gait: List[GaitSeriesPoint]
    recent_reports: List[ReportSeriesPoint]


class SurgeryTypeBreakdown(BaseModel):
    surgery_type: str
    patient_count: int


class RiskPatient(BaseModel):
    patient_id: str
    first_name: str
    last_name: str
    surgery_type: str
    latest_recovery_score: int
    latest_recovery_status: str
    last_report_date: date


class RecoveryBucket(BaseModel):
    bucket: str  # "Good" | "Moderate" | "Needs Attention" | "No data"
    patient_count: int


class AdminAnalyticsOut(BaseModel):
    total_patients: int
    total_clinicians: int
    total_gait_records: int
    total_reports: int
    average_recovery_score: float
    surgery_type_breakdown: List[SurgeryTypeBreakdown]
    recovery_distribution: List[RecoveryBucket]
    top_risk_patients: List[RiskPatient]
    patients_active_last_7_days: int