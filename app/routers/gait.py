from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, GaitRecord
from app.schemas import GaitRecordCreate, GaitRecordOut
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/gait-data", tags=["Gait Data"])


@router.post("/", response_model=GaitRecordOut)
def create_gait_record(
    payload: GaitRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("patient", "admin")),
):
    record = GaitRecord(
        user_id=current_user.id,
        record_date=payload.record_date,
        step_count=payload.step_count,
        walking_speed=payload.walking_speed,
        cadence=payload.cadence,
        distance=payload.distance,
        active_minutes=payload.active_minutes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/", response_model=list[GaitRecordOut])
def get_my_gait_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("patient", "admin")),
):
    records = (
        db.query(GaitRecord)
        .filter(GaitRecord.user_id == current_user.id)
        .order_by(GaitRecord.record_date.desc())
        .all()
    )
    return records


@router.get("/patient/{patient_id}", response_model=list[GaitRecordOut])
def get_patient_gait_records(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("clinician", "admin")),
):
    patient = db.query(User).filter(User.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    records = (
        db.query(GaitRecord)
        .filter(GaitRecord.user_id == patient.id)
        .order_by(GaitRecord.record_date.desc())
        .all()
    )
    return records