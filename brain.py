"""
brain.py — simulated hardware "brain" for Orthoreco.

Acts like a wearable sensor unit (IMU + pedometer) strapped to a recovering
patient. Logs into the Orthoreco API, generates plausible gait readings, and
POSTs them to /gait-data/ on a configurable interval.

Usage:
    python brain.py --email patient@example.com --password secret
    python brain.py --email a@b.com --password p --interval 5 --days 14
    python brain.py --email a@b.com --password p --once

Sensors simulated:
    - step_count       (pedometer)
    - walking_speed    (m/s, IMU-derived)
    - cadence          (steps/min, IMU)
    - distance         (km, derived)
    - active_minutes   (activity classifier)

Recovery model: readings start low post-surgery and improve over time with
day-to-day noise, mimicking what a real sensor would observe on a patient
following a rehab plan.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta


DEFAULT_BASE_URL = os.environ.get("ORTHORECO_BASE_URL", "http://127.0.0.1:8000")


def login(base_url: str, email: str, password: str) -> str:
    """Hit /auth/login (OAuth2 password form) and return access_token."""
    url = f"{base_url.rstrip('/')}/auth/login"
    form = urllib.parse.urlencode({
        "username": email,
        "password": password,
    }).encode()

    req = urllib.request.Request(
        url,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode())
    return body["access_token"]


def simulate_reading(day_index: int, total_days: int) -> dict:
    """
    Generate one day of fake sensor data.

    day_index 0 = day of surgery (worst). Higher = more recovered.
    """
    # progress 0..1 over recovery window, soft sigmoid curve
    progress = 1 / (1 + math.exp(-0.25 * (day_index - total_days / 3)))

    base_steps = 400 + progress * 9000
    step_count = max(0, int(random.gauss(base_steps, base_steps * 0.15)))

    base_speed = 0.35 + progress * 0.95     # m/s
    walking_speed = round(max(0.1, random.gauss(base_speed, 0.07)), 2)

    base_cadence = 45 + progress * 65       # steps/min
    cadence = round(max(20.0, random.gauss(base_cadence, 4.0)), 1)

    # ~0.7 m per step, convert to km
    distance = round(step_count * 0.0007, 2)

    base_active = 8 + progress * 55         # minutes
    active_minutes = max(0, int(random.gauss(base_active, 6)))

    return {
        "step_count": step_count,
        "walking_speed": walking_speed,
        "cadence": cadence,
        "distance": distance,
        "active_minutes": active_minutes,
    }


def post_gait(base_url: str, token: str, payload: dict) -> dict:
    url = f"{base_url.rstrip('/')}/gait-data/"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def run(args: argparse.Namespace) -> int:
    print(f"[brain] connecting to {args.base_url} as {args.email}")
    try:
        token = login(args.base_url, args.email, args.password)
    except urllib.error.HTTPError as e:
        print(f"[brain] login failed: {e.code} {e.read().decode()}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"[brain] cannot reach API: {e.reason}", file=sys.stderr)
        return 1
    print("[brain] login ok, sensors online")

    today = date.today()

    # --once / --today: single reading dated today, treated as latest day in
    # recovery window (most recovered point on the curve).
    if args.once or args.today:
        reading = simulate_reading(day_index=args.days - 1, total_days=args.days)
        reading["record_date"] = today.isoformat()
        return _send_one(args.base_url, token, today, reading)

    # Backfill mode: N consecutive days ending today.
    start = today - timedelta(days=args.days - 1)
    rc = 0
    for i in range(args.days):
        record_date = start + timedelta(days=i)
        reading = simulate_reading(day_index=i, total_days=args.days)
        reading["record_date"] = record_date.isoformat()
        rc |= _send_one(args.base_url, token, record_date, reading)

        if i < args.days - 1 and args.interval > 0:
            time.sleep(args.interval)

    print("[brain] done")
    return rc


def _send_one(base_url: str, token: str, record_date: date, reading: dict) -> int:
    try:
        saved = post_gait(base_url, token, reading)
        print(
            f"[brain] {record_date}  steps={reading['step_count']:>5}  "
            f"speed={reading['walking_speed']}m/s  "
            f"cadence={reading['cadence']}  "
            f"dist={reading['distance']}km  "
            f"active={reading['active_minutes']}min  "
            f"-> id={saved.get('id')}"
        )
        return 0
    except urllib.error.HTTPError as e:
        print(
            f"[brain] POST failed on {record_date}: {e.code} {e.read().decode()}",
            file=sys.stderr,
        )
        return 1


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Orthoreco hardware sensor simulator")
    p.add_argument(
        "--email",
        default=os.environ.get("ORTHORECO_EMAIL"),
        help="Patient login email (or env ORTHORECO_EMAIL)",
    )
    p.add_argument(
        "--password",
        default=os.environ.get("ORTHORECO_PASSWORD"),
        help="Patient password (or env ORTHORECO_PASSWORD)",
    )
    p.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    p.add_argument("--days", type=int, default=7, help="Recovery-window length in days")
    p.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Seconds to wait between sends in backfill mode (0 = blast)",
    )
    p.add_argument(
        "--once",
        action="store_true",
        help="Send a single reading dated today, then exit (use for cron)",
    )
    p.add_argument(
        "--today",
        action="store_true",
        help="Alias of --once: send today's reading and exit",
    )
    p.add_argument("--seed", type=int, default=None, help="Optional RNG seed")

    args = p.parse_args()
    if not args.email or not args.password:
        p.error("email and password required (flags or ORTHORECO_EMAIL/ORTHORECO_PASSWORD)")
    return args


if __name__ == "__main__":
    args = parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    sys.exit(run(args))
