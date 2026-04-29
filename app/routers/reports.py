from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PatientReport, User
from app.schemas import PatientReportCreate, PatientReportOut, PatientReportSummaryOut
from app.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Patient Reports"])


def calculate_recovery_score(report: PatientReport):
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
        message = "Recovery looks positive. Keep following the care plan."
    elif score >= 45:
        status_text = "Moderate"
        message = "Recovery is progressing, but symptoms should still be monitored."
    else:
        status_text = "Needs Attention"
        message = "Symptoms suggest slower recovery. Contact clinician if this continues."

    return score, status_text, message


def report_to_summary(report: PatientReport):
    score, status_text, message = calculate_recovery_score(report)

    return PatientReportSummaryOut(
        id=report.id,
        user_id=report.user_id,
        report_date=report.report_date,
        pain_score=report.pain_score,
        stiffness_score=report.stiffness_score,
        walking_difficulty=report.walking_difficulty,
        confidence_score=report.confidence_score,
        swelling_flag=report.swelling_flag,
        exercise_completed=report.exercise_completed,
        notes=report.notes,
        created_at=report.created_at,
        recovery_score=score,
        recovery_status=status_text,
        recovery_message=message,
    )


@router.post("/", response_model=PatientReportSummaryOut, status_code=status.HTTP_201_CREATED)
def create_report(
    report_data: PatientReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_report = (
        db.query(PatientReport)
        .filter(
            PatientReport.user_id == current_user.id,
            PatientReport.report_date == report_data.report_date,
        )
        .first()
    )

    if existing_report:
        raise HTTPException(
            status_code=400,
            detail="You have already submitted a check-in for this date.",
        )

    new_report = PatientReport(
        user_id=current_user.id,
        report_date=report_data.report_date,
        pain_score=report_data.pain_score,
        stiffness_score=report_data.stiffness_score,
        walking_difficulty=report_data.walking_difficulty,
        confidence_score=report_data.confidence_score,
        swelling_flag=report_data.swelling_flag,
        exercise_completed=report_data.exercise_completed,
        notes=report_data.notes,
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return report_to_summary(new_report)


@router.get("/me", response_model=List[PatientReportSummaryOut])
def get_my_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reports = (
        db.query(PatientReport)
        .filter(PatientReport.user_id == current_user.id)
        .order_by(PatientReport.report_date.desc())
        .all()
    )

    return [report_to_summary(report) for report in reports]


@router.get("/patient/{patient_id}", response_model=List[PatientReportSummaryOut])
def get_patient_reports(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reports = (
        db.query(PatientReport)
        .filter(PatientReport.user_id == patient_id)
        .order_by(PatientReport.report_date.desc())
        .all()
    )

    return [report_to_summary(report) for report in reports]