from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, GaitRecord
from app.schemas import (
    PatientDashboard,
    ClinicianPatientSummary,
    ClinicianDashboard,
)
from app.auth import require_roles

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/patient", response_model=PatientDashboard)
def patient_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("patient", "admin")),
):
    latest_record = (
        db.query(GaitRecord)
        .filter(GaitRecord.user_id == current_user.id)
        .order_by(GaitRecord.record_date.desc())
        .first()
    )

    total_records = (
        db.query(func.count(GaitRecord.id))
        .filter(GaitRecord.user_id == current_user.id)
        .scalar()
    ) or 0

    avg_step_count = (
        db.query(func.avg(GaitRecord.step_count))
        .filter(GaitRecord.user_id == current_user.id)
        .scalar()
    ) or 0.0

    avg_walking_speed = (
        db.query(func.avg(GaitRecord.walking_speed))
        .filter(GaitRecord.user_id == current_user.id)
        .scalar()
    )

    avg_cadence = (
        db.query(func.avg(GaitRecord.cadence))
        .filter(GaitRecord.user_id == current_user.id)
        .scalar()
    )

    return PatientDashboard(
        patient_id=current_user.patient_id,
        surgery_type=current_user.surgery_type,
        surgery_side=current_user.surgery_side,
        total_records=total_records,
        latest_record=latest_record,
        average_step_count=float(avg_step_count),
        average_walking_speed=float(avg_walking_speed) if avg_walking_speed is not None else None,
        average_cadence=float(avg_cadence) if avg_cadence is not None else None,
    )


@router.get("/clinician", response_model=ClinicianDashboard)
def clinician_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("clinician", "admin")),
):
    patients = db.query(User).filter(User.role == "patient").all()

    patient_summaries = []
    total_gait_records = 0

    for patient in patients:
        record_count = (
            db.query(func.count(GaitRecord.id))
            .filter(GaitRecord.user_id == patient.id)
            .scalar()
        ) or 0

        total_gait_records += record_count

        patient_summaries.append(
            ClinicianPatientSummary(
                patient_id=patient.patient_id,
                email=patient.email,
                surgery_type=patient.surgery_type,
                surgery_side=patient.surgery_side,
                total_records=record_count,
            )
        )

    return ClinicianDashboard(
        total_patients=len(patients),
        total_gait_records=total_gait_records,
        patients=patient_summaries,
    )


@router.get("/clinician/patient/{patient_id}")
def clinician_patient_dashboard(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("clinician", "admin")),
):
    patient = db.query(User).filter(User.patient_id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    latest_record = (
        db.query(GaitRecord)
        .filter(GaitRecord.user_id == patient.id)
        .order_by(GaitRecord.record_date.desc())
        .first()
    )

    total_records = (
        db.query(func.count(GaitRecord.id))
        .filter(GaitRecord.user_id == patient.id)
        .scalar()
    ) or 0

    avg_step_count = (
        db.query(func.avg(GaitRecord.step_count))
        .filter(GaitRecord.user_id == patient.id)
        .scalar()
    ) or 0.0

    avg_walking_speed = (
        db.query(func.avg(GaitRecord.walking_speed))
        .filter(GaitRecord.user_id == patient.id)
        .scalar()
    )

    avg_cadence = (
        db.query(func.avg(GaitRecord.cadence))
        .filter(GaitRecord.user_id == patient.id)
        .scalar()
    )

    return {
        "patient_id": patient.patient_id,
        "email": patient.email,
        "surgery_type": patient.surgery_type,
        "surgery_side": patient.surgery_side,
        "total_records": total_records,
        "latest_record": latest_record,
        "average_step_count": float(avg_step_count),
        "average_walking_speed": float(avg_walking_speed) if avg_walking_speed is not None else None,
        "average_cadence": float(avg_cadence) if avg_cadence is not None else None,
    }