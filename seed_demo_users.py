"""
seed_demo_users.py — create demo admin and clinician accounts.

Run from project root:
    python seed_demo_users.py

Idempotent: if a demo account already exists, the password is reset to
the documented default but no duplicate row is created.
"""

from app.database import SessionLocal
from app.models import User
from app.auth import hash_password


DEMO_USERS = [
    {
        "email": "admin@demo.com",
        "password": "admin123",
        "first_name": "Demo",
        "last_name": "Admin",
        "gender": "Other",
        "patient_id": "ADMIN001",
        "surgery_type": "n/a",
        "surgery_side": "n/a",
        "role": "admin",
    },
    {
        "email": "doctor@demo.com",
        "password": "doctor123",
        "first_name": "Demo",
        "last_name": "Doctor",
        "gender": "Other",
        "patient_id": "DOC001",
        "surgery_type": "n/a",
        "surgery_side": "n/a",
        "role": "clinician",
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        for spec in DEMO_USERS:
            existing = db.query(User).filter(User.email == spec["email"]).first()
            if existing:
                existing.role = spec["role"]
                existing.password_hash = hash_password(spec["password"])
                action = "updated"
            else:
                db.add(User(
                    first_name=spec["first_name"],
                    last_name=spec["last_name"],
                    gender=spec["gender"],
                    patient_id=spec["patient_id"],
                    email=spec["email"],
                    password_hash=hash_password(spec["password"]),
                    surgery_type=spec["surgery_type"],
                    surgery_side=spec["surgery_side"],
                    role=spec["role"],
                ))
                action = "created"

            print(f"[seed] {action:7s} {spec['role']:9s} {spec['email']}  (password: {spec['password']})")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
