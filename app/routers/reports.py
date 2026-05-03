from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PatientReport, User
from app.schemas import (
    PatientReportCreate,
    PatientReportOut,
    PatientReportSummaryOut,
    WeeklyRecoverySummaryOut,
)
from app.auth import get_current_user
from datetime import date, timedelta

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


@router.get("/me/weekly-summary", response_model=WeeklyRecoverySummaryOut)
def get_my_weekly_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    start_date = today - timedelta(days=6)

    reports = (
        db.query(PatientReport)
        .filter(
            PatientReport.user_id == current_user.id,
            PatientReport.report_date >= start_date,
            PatientReport.report_date <= today,
        )
        .order_by(PatientReport.report_date.asc())
        .all()
    )

    report_dates = {report.report_date for report in reports}

    expected_dates = [
        start_date + timedelta(days=i)
        for i in range(7)
    ]

    missing_dates = [
        d.isoformat()
        for d in expected_dates
        if d not in report_dates
    ]

    total_checkins = len(reports)

    if total_checkins == 0:
        return WeeklyRecoverySummaryOut(
            total_checkins=0,
            average_pain=0,
            average_stiffness=0,
            average_walking_difficulty=0,
            average_confidence=0,
            exercise_completion_percentage=0,
            swelling_days=0,
            missing_dates=missing_dates,
            missed_days_count=len(missing_dates),
            current_streak=0,
            trend_message="No check-ins were submitted this week.",
            risk_message="Submit daily check-ins to generate recovery insights.",
        )

    average_pain = sum(r.pain_score for r in reports) / total_checkins
    average_stiffness = sum(r.stiffness_score for r in reports) / total_checkins
    average_walking = sum(r.walking_difficulty for r in reports) / total_checkins
    average_confidence = sum(r.confidence_score for r in reports) / total_checkins

    exercise_completed = sum(1 for r in reports if r.exercise_completed)
    exercise_completion_percentage = (exercise_completed / total_checkins) * 100

    swelling_days = sum(1 for r in reports if r.swelling_flag)

    # Current streak: count backwards from today
    current_streak = 0
    check_date = today

    while check_date in report_dates:
        current_streak += 1
        check_date -= timedelta(days=1)

    # Trend logic
    trend_message = "Not enough data to detect a clear trend yet."

    if total_checkins >= 2:
        first_report = reports[0]
        latest_report = reports[-1]

        pain_change = latest_report.pain_score - first_report.pain_score
        confidence_change = latest_report.confidence_score - first_report.confidence_score
        walking_change = latest_report.walking_difficulty - first_report.walking_difficulty

        if pain_change < 0 and confidence_change > 0:
            trend_message = "Your pain is decreasing and confidence is improving this week."
        elif pain_change > 0 or walking_change > 0:
            trend_message = "Some symptoms appear to be worsening this week. Keep monitoring your recovery."
        elif pain_change == 0 and walking_change == 0:
            trend_message = "Your symptoms appear stable this week."
        else:
            trend_message = "Your recovery shows mixed changes this week."

    # Risk logic
    risk_message = "Your weekly recovery indicators look stable."

    latest_report = reports[-1]

    if latest_report.pain_score >= 8 and latest_report.swelling_flag:
        risk_message = "High pain and swelling were reported. Consider contacting your clinician if this continues."
    elif len(missing_dates) >= 3:
        risk_message = "Several check-ins were missed this week. Daily tracking is recommended."
    elif average_pain >= 7:
        risk_message = "Average pain is high this week. Continue monitoring symptoms closely."
    elif swelling_days >= 3:
        risk_message = "Swelling was reported on multiple days this week."

    return WeeklyRecoverySummaryOut(
        total_checkins=total_checkins,
        average_pain=round(average_pain, 1),
        average_stiffness=round(average_stiffness, 1),
        average_walking_difficulty=round(average_walking, 1),
        average_confidence=round(average_confidence, 1),
        exercise_completion_percentage=round(exercise_completion_percentage, 1),
        swelling_days=swelling_days,
        missing_dates=missing_dates,
        missed_days_count=len(missing_dates),
        current_streak=current_streak,
        trend_message=trend_message,
        risk_message=risk_message,
    )