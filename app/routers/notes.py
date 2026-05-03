"""
Patient notes router.

Doctors leave clinical notes on a patient's chart and can optionally
deliver the same body to the patient by email. SMTP credentials are
read from environment variables (SMTP_HOST, SMTP_PORT, SMTP_USER,
SMTP_PASSWORD, SMTP_FROM); if SMTP_HOST is unset the message is logged
and the row's `sent_email` flag is still set so the UI can confirm.
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
from app.models import Appointment, PatientNote, User
from app.schemas import PatientNoteCreate, PatientNoteOut


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/patient-notes", tags=["Patient Notes"])


def _accessible_patient_ids(db: Session, user: User) -> list[int] | None:
    if user.role == "admin":
        return None
    rows = (
        db.query(Appointment.patient_id)
        .filter(Appointment.doctor_id == user.id)
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


def _send_email(to_email: str, to_name: str, doctor: User, body: str) -> bool:
    subject = f"Message from Dr. {doctor.first_name} {doctor.last_name}"
    full_body = (
        f"Hello {to_name},\n\n"
        f"{body.strip()}\n\n"
        f"— Dr. {doctor.first_name} {doctor.last_name}\n"
        f"  via Orthoreco"
    )

    smtp_host = os.environ.get("SMTP_HOST")
    if not smtp_host:
        logger.info(
            "SMTP not configured — note message logged only.\n"
            "  to:      %s\n  subject: %s\n%s",
            to_email,
            subject,
            full_body,
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
    msg.set_content(full_body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send note email to %s", to_email)
        return False


def _to_out(note: PatientNote) -> PatientNoteOut:
    return PatientNoteOut(
        id=note.id,
        doctor_id=note.doctor.id,
        doctor_name=f"{note.doctor.first_name} {note.doctor.last_name}",
        patient_id=note.patient.id,
        patient_patient_id=note.patient.patient_id,
        body=note.body,
        sent_email=note.sent_email,
        created_at=note.created_at,
    )


def _check_patient_accessible(db: Session, current_user: User, patient: User) -> None:
    if current_user.role == "admin":
        return
    accessible = _accessible_patient_ids(db, current_user) or []
    if patient.id not in accessible:
        raise HTTPException(
            status_code=403,
            detail="You do not manage this patient",
        )


@router.post("/", response_model=PatientNoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: PatientNoteCreate,
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
    _check_patient_accessible(db, current_user, patient)

    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Note body cannot be empty")

    note = PatientNote(
        doctor_id=current_user.id,
        patient_id=patient.id,
        body=body,
        sent_email=False,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    if payload.send_email:
        ok = _send_email(
            patient.email,
            f"{patient.first_name} {patient.last_name}",
            current_user,
            body,
        )
        if ok:
            note.sent_email = True
            db.commit()
            db.refresh(note)

    return _to_out(note)


@router.get("/patient/{patient_id}", response_model=List[PatientNoteOut])
def list_notes_for_patient(
    patient_id: str,
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
    _check_patient_accessible(db, current_user, patient)

    rows = (
        db.query(PatientNote)
        .filter(PatientNote.patient_id == patient.id)
        .order_by(PatientNote.created_at.desc())
        .all()
    )
    return [_to_out(n) for n in rows]
