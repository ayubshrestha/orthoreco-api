"""
Appointments router.

Clinicians (and admins) can schedule appointments with patients and
optionally send the patient an email invitation. SMTP credentials are
read from environment variables (SMTP_HOST, SMTP_PORT, SMTP_USER,
SMTP_PASSWORD, SMTP_FROM). If SMTP_HOST is not set the email body is
written to the server log instead — the appointment row still gets
`invitation_sent=True` so the UI can confirm the action.
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.database import get_db
from app.models import Appointment, User
from app.schemas import AppointmentCreate, AppointmentOut


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/appointments", tags=["Appointments"])


def _send_invite_email(to_email: str, to_name: str, doctor: User, appt: Appointment) -> bool:
    """Best-effort send. Returns True if SMTP was attempted (or stub-logged)."""
    subject = f"Appointment invitation from Dr. {doctor.first_name} {doctor.last_name}"
    body = (
        f"Hello {to_name},\n\n"
        f"Dr. {doctor.first_name} {doctor.last_name} has scheduled a "
        f"follow-up appointment for you.\n\n"
        f"  When:     {appt.scheduled_for.strftime('%Y-%m-%d %H:%M')}\n"
        f"  Where:    {appt.location or 'TBD'}\n"
        f"  Notes:    {appt.notes or '(none)'}\n\n"
        f"Please reply to confirm or contact the clinic if you cannot attend.\n\n"
        f"— Orthoreco"
    )

    smtp_host = os.environ.get("SMTP_HOST")
    if not smtp_host:
        logger.info(
            "SMTP not configured — invitation logged only.\n"
            "  to:      %s\n  subject: %s\n%s",
            to_email,
            subject,
            body,
        )
        return True

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASSWORD")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user or "noreply@orthoreco.local")

    msg = EmailMessage()
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send invitation email to %s", to_email)
        return False


def _to_out(appt: Appointment) -> AppointmentOut:
    return AppointmentOut(
        id=appt.id,
        doctor_id=appt.doctor.id,
        doctor_name=f"{appt.doctor.first_name} {appt.doctor.last_name}",
        doctor_email=appt.doctor.email,
        patient_id=appt.patient.id,
        patient_patient_id=appt.patient.patient_id,
        patient_first_name=appt.patient.first_name,
        patient_last_name=appt.patient.last_name,
        patient_email=appt.patient.email,
        scheduled_for=appt.scheduled_for,
        location=appt.location,
        notes=appt.notes,
        status=appt.status,
        invitation_sent=appt.invitation_sent,
        created_at=appt.created_at,
    )


@router.post("/", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("clinician", "admin")),
):
    patient = (
        db.query(User)
        .filter(User.patient_id == payload.patient_id, User.role == "patient")
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    appt = Appointment(
        doctor_id=current_user.id,
        patient_id=patient.id,
        scheduled_for=payload.scheduled_for,
        location=payload.location,
        notes=payload.notes,
        status="pending",
        invitation_sent=False,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    if payload.send_email:
        sent = _send_invite_email(
            patient.email,
            f"{patient.first_name} {patient.last_name}",
            current_user,
            appt,
        )
        if sent:
            appt.invitation_sent = True
            db.commit()
            db.refresh(appt)

    return _to_out(appt)


@router.get("/me", response_model=List[AppointmentOut])
def my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("clinician", "admin")),
):
    rows = (
        db.query(Appointment)
        .filter(Appointment.doctor_id == current_user.id)
        .order_by(Appointment.scheduled_for.desc())
        .all()
    )
    return [_to_out(a) for a in rows]


@router.get("/all", response_model=List[AppointmentOut])
def all_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    rows = (
        db.query(Appointment).order_by(Appointment.scheduled_for.desc()).all()
    )
    return [_to_out(a) for a in rows]
