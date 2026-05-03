from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, GaitRecord, PatientReport
from app.schemas import (
    PatientDashboard,
    ClinicianPatientSummary,
    ClinicianDashboard,
    PatientTableRow,
    PatientDetailOut,
    GaitSeriesPoint,
    ReportSeriesPoint,
    AdminAnalyticsOut,
    SurgeryTypeBreakdown,
    RecoveryBucket,
    RiskPatient,
)
from app.auth import require_roles

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ---------------------------------------------------------------------------
# Recovery scoring (kept here so dashboard does not depend on the reports router)
# ---------------------------------------------------------------------------


def _score_report(report: PatientReport) -> tuple[int, str]:
    score = 100
    score -= report.pain_score * 5
    score -= report.stiffness_score * 3
    score -= report.walking_difficulty * 4
    score += report.confidence_score * 3
    if report.swelling_flag:
        score -= 10
    if report.exercise_completed:
        score += 5
    score = max(0, min(100, score))

    if score >= 75:
        status_text = "Good"
    elif score >= 45:
        status_text = "Moderate"
    else:
        status_text = "Needs Attention"
    return score, status_text


def _build_table_row(db: Session, patient: User) -> PatientTableRow:
    total_gait = (
        db.query(func.count(GaitRecord.id))
        .filter(GaitRecord.user_id == patient.id)
        .scalar()
    ) or 0

    total_reports = (
        db.query(func.count(PatientReport.id))
        .filter(PatientReport.user_id == patient.id)
        .scalar()
    ) or 0

    last_gait = (
        db.query(func.max(GaitRecord.record_date))
        .filter(GaitRecord.user_id == patient.id)
        .scalar()
    )

    latest_report = (
        db.query(PatientReport)
        .filter(PatientReport.user_id == patient.id)
        .order_by(PatientReport.report_date.desc())
        .first()
    )

    if latest_report:
        score, status_text = _score_report(latest_report)
        last_report_date = latest_report.report_date
    else:
        score, status_text, last_report_date = None, None, None

    days_since_surgery = (
        (date.today() - patient.surgery_date).days
        if patient.surgery_date else None
    )

    return PatientTableRow(
        id=patient.id,
        patient_id=patient.patient_id,
        first_name=patient.first_name,
        last_name=patient.last_name,
        email=patient.email,
        gender=patient.gender,
        date_of_birth=patient.date_of_birth,
        surgery_type=patient.surgery_type,
        surgery_side=patient.surgery_side,
        surgery_date=patient.surgery_date,
        days_since_surgery=days_since_surgery,
        total_gait_records=total_gait,
        total_reports=total_reports,
        last_gait_date=last_gait,
        last_report_date=last_report_date,
        latest_recovery_score=score,
        latest_recovery_status=status_text,
    )


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


# ===========================================================================
# Admin / clinician dashboard
# ===========================================================================


@router.get("/admin/patients", response_model=List[PatientTableRow])
def admin_patient_table(
    surgery_type: Optional[str] = Query(None, description="Filter by surgery type"),
    search: Optional[str] = Query(None, description="Search by name, email, or patient_id"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("clinician", "admin")),
):
    """Table view: every patient with summary stats and latest recovery state."""
    q = db.query(User).filter(User.role == "patient")

    if surgery_type:
        q = q.filter(User.surgery_type == surgery_type)

    if search:
        like = f"%{search}%"
        q = q.filter(
            (User.first_name.ilike(like))
            | (User.last_name.ilike(like))
            | (User.email.ilike(like))
            | (User.patient_id.ilike(like))
        )

    patients = q.order_by(User.last_name.asc(), User.first_name.asc()).all()
    return [_build_table_row(db, p) for p in patients]


@router.get("/admin/patients/{patient_id}", response_model=PatientDetailOut)
def admin_patient_detail(
    patient_id: str,
    days: int = Query(30, ge=1, le=365, description="History window in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("clinician", "admin")),
):
    patient = (
        db.query(User)
        .filter(User.patient_id == patient_id, User.role == "patient")
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    cutoff = date.today() - timedelta(days=days - 1)

    gait_rows = (
        db.query(GaitRecord)
        .filter(
            GaitRecord.user_id == patient.id,
            GaitRecord.record_date >= cutoff,
        )
        .order_by(GaitRecord.record_date.asc())
        .all()
    )

    report_rows = (
        db.query(PatientReport)
        .filter(
            PatientReport.user_id == patient.id,
            PatientReport.report_date >= cutoff,
        )
        .order_by(PatientReport.report_date.asc())
        .all()
    )

    recent_reports = []
    for r in report_rows:
        score, status_text = _score_report(r)
        recent_reports.append(
            ReportSeriesPoint(
                report_date=r.report_date,
                pain_score=r.pain_score,
                stiffness_score=r.stiffness_score,
                walking_difficulty=r.walking_difficulty,
                confidence_score=r.confidence_score,
                swelling_flag=r.swelling_flag,
                exercise_completed=r.exercise_completed,
                recovery_score=score,
                recovery_status=status_text,
            )
        )

    return PatientDetailOut(
        profile=_build_table_row(db, patient),
        recent_gait=[
            GaitSeriesPoint(
                record_date=g.record_date,
                step_count=g.step_count,
                walking_speed=g.walking_speed,
                cadence=g.cadence,
                distance=g.distance,
                active_minutes=g.active_minutes,
            )
            for g in gait_rows
        ],
        recent_reports=recent_reports,
    )


@router.get(
    "/admin/patients/{patient_id}/gait-series",
    response_model=List[GaitSeriesPoint],
)
def admin_patient_gait_series(
    patient_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("clinician", "admin")),
):
    """Time-series of daily gait readings for graphing."""
    patient = (
        db.query(User)
        .filter(User.patient_id == patient_id, User.role == "patient")
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    cutoff = date.today() - timedelta(days=days - 1)

    rows = (
        db.query(GaitRecord)
        .filter(
            GaitRecord.user_id == patient.id,
            GaitRecord.record_date >= cutoff,
        )
        .order_by(GaitRecord.record_date.asc())
        .all()
    )

    return [
        GaitSeriesPoint(
            record_date=g.record_date,
            step_count=g.step_count,
            walking_speed=g.walking_speed,
            cadence=g.cadence,
            distance=g.distance,
            active_minutes=g.active_minutes,
        )
        for g in rows
    ]


@router.get(
    "/admin/patients/{patient_id}/reports-series",
    response_model=List[ReportSeriesPoint],
)
def admin_patient_reports_series(
    patient_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("clinician", "admin")),
):
    """Time-series of daily check-ins with recovery scores for graphing."""
    patient = (
        db.query(User)
        .filter(User.patient_id == patient_id, User.role == "patient")
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    cutoff = date.today() - timedelta(days=days - 1)

    rows = (
        db.query(PatientReport)
        .filter(
            PatientReport.user_id == patient.id,
            PatientReport.report_date >= cutoff,
        )
        .order_by(PatientReport.report_date.asc())
        .all()
    )

    out = []
    for r in rows:
        score, status_text = _score_report(r)
        out.append(
            ReportSeriesPoint(
                report_date=r.report_date,
                pain_score=r.pain_score,
                stiffness_score=r.stiffness_score,
                walking_difficulty=r.walking_difficulty,
                confidence_score=r.confidence_score,
                swelling_flag=r.swelling_flag,
                exercise_completed=r.exercise_completed,
                recovery_score=score,
                recovery_status=status_text,
            )
        )
    return out


@router.get("/admin/analytics", response_model=AdminAnalyticsOut)
def admin_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("clinician", "admin")),
):
    """Aggregate KPIs across all patients."""
    total_patients = (
        db.query(func.count(User.id)).filter(User.role == "patient").scalar()
    ) or 0
    total_clinicians = (
        db.query(func.count(User.id)).filter(User.role == "clinician").scalar()
    ) or 0
    total_gait = db.query(func.count(GaitRecord.id)).scalar() or 0
    total_reports = db.query(func.count(PatientReport.id)).scalar() or 0

    # Surgery-type distribution
    surgery_rows = (
        db.query(User.surgery_type, func.count(User.id))
        .filter(User.role == "patient")
        .group_by(User.surgery_type)
        .all()
    )
    surgery_breakdown = [
        SurgeryTypeBreakdown(surgery_type=row[0], patient_count=row[1])
        for row in surgery_rows
    ]

    # Per-patient latest report → recovery score, used for distribution + risk list
    patients = db.query(User).filter(User.role == "patient").all()

    buckets = {"Good": 0, "Moderate": 0, "Needs Attention": 0, "No data": 0}
    score_total = 0
    score_count = 0
    risk_candidates: list[RiskPatient] = []

    for p in patients:
        latest = (
            db.query(PatientReport)
            .filter(PatientReport.user_id == p.id)
            .order_by(PatientReport.report_date.desc())
            .first()
        )
        if not latest:
            buckets["No data"] += 1
            continue

        score, status_text = _score_report(latest)
        buckets[status_text] += 1
        score_total += score
        score_count += 1

        if status_text == "Needs Attention":
            risk_candidates.append(
                RiskPatient(
                    patient_id=p.patient_id,
                    first_name=p.first_name,
                    last_name=p.last_name,
                    surgery_type=p.surgery_type,
                    latest_recovery_score=score,
                    latest_recovery_status=status_text,
                    last_report_date=latest.report_date,
                )
            )

    # Sort risk patients worst-first, cap at 10
    risk_candidates.sort(key=lambda r: r.latest_recovery_score)
    top_risk = risk_candidates[:10]

    avg_score = round(score_total / score_count, 1) if score_count else 0.0

    # Active in last 7 days = at least one gait record in window
    week_ago = date.today() - timedelta(days=6)
    active_rows = (
        db.query(GaitRecord.user_id)
        .filter(GaitRecord.record_date >= week_ago)
        .distinct()
        .count()
    )

    return AdminAnalyticsOut(
        total_patients=total_patients,
        total_clinicians=total_clinicians,
        total_gait_records=total_gait,
        total_reports=total_reports,
        average_recovery_score=avg_score,
        surgery_type_breakdown=surgery_breakdown,
        recovery_distribution=[
            RecoveryBucket(bucket=b, patient_count=c) for b, c in buckets.items()
        ],
        top_risk_patients=top_risk,
        patients_active_last_7_days=active_rows,
    )