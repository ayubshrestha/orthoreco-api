"""
brain.py — simulated hardware "brain" for Orthoreco.

Acts like a wearable sensor unit (IMU + pedometer) strapped to a recovering
patient. Logs into the Orthoreco API, generates plausible gait readings, and
POSTs them to /gait-data/.

Modes:
    backfill (default): seed N consecutive past days
    --once / --today  : single reading dated today, then exit (use for cron)
    --simulate        : long-running daemon, ticks every --tick seconds
                        through a sit/stand/walk/exercise state machine,
                        accumulates into today's row, rolls over at midnight

Sensors simulated:
    - step_count       (pedometer, cumulative for the day)
    - walking_speed    (m/s, IMU-derived, rolling average over walking ticks)
    - cadence          (steps/min, IMU, rolling average over walking ticks)
    - distance         (km, derived from steps)
    - active_minutes   (minutes spent not sitting)
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
from datetime import date, datetime, timedelta


DEFAULT_BASE_URL = os.environ.get("ORTHORECO_BASE_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


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
        return json.loads(resp.read().decode())["access_token"]


def fetch_me(base_url: str, token: str) -> dict:
    url = f"{base_url.rstrip('/')}/auth/me"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def post_gait(base_url: str, token: str, payload: dict) -> dict:
    url = f"{base_url.rstrip('/')}/gait-data/"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# Daily-summary simulator (used by --once and backfill)
# ---------------------------------------------------------------------------


def simulate_reading(day_index: int, total_days: int) -> dict:
    """
    Generate one whole-day summary.

    day_index 0 = day of surgery (worst). Higher = more recovered.
    """
    progress = 1 / (1 + math.exp(-0.25 * (day_index - total_days / 3)))

    base_steps = 400 + progress * 9000
    step_count = max(0, int(random.gauss(base_steps, base_steps * 0.15)))

    base_speed = 0.35 + progress * 0.95
    walking_speed = round(max(0.1, random.gauss(base_speed, 0.07)), 2)

    base_cadence = 45 + progress * 65
    cadence = round(max(20.0, random.gauss(base_cadence, 4.0)), 1)

    distance = round(step_count * 0.0007, 2)

    base_active = 8 + progress * 55
    active_minutes = max(0, int(random.gauss(base_active, 6)))

    return {
        "step_count": step_count,
        "walking_speed": walking_speed,
        "cadence": cadence,
        "distance": distance,
        "active_minutes": active_minutes,
    }


# ---------------------------------------------------------------------------
# Continuous-activity simulator (used by --simulate)
# ---------------------------------------------------------------------------

# Markov-ish transition table over activity states.
# Probabilities tuned to a recovering patient: lots of sitting, occasional
# walking, light exercise sessions, no running.
TRANSITIONS = {
    "sit":      [("sit", 0.55), ("stand", 0.25), ("walk", 0.15), ("exercise", 0.05)],
    "stand":    [("sit", 0.30), ("stand", 0.25), ("walk", 0.40), ("exercise", 0.05)],
    "walk":     [("sit", 0.25), ("stand", 0.20), ("walk", 0.50), ("exercise", 0.05)],
    "exercise": [("sit", 0.50), ("stand", 0.20), ("walk", 0.20), ("exercise", 0.10)],
}


def next_state(current: str) -> str:
    r = random.random()
    cum = 0.0
    for state, p in TRANSITIONS[current]:
        cum += p
        if r <= cum:
            return state
    return TRANSITIONS[current][-1][0]


def days_since_surgery(profile: dict) -> int:
    sd = profile.get("surgery_date")
    if not sd:
        return 30  # assume mid-recovery if unknown
    try:
        d = date.fromisoformat(sd)
    except ValueError:
        return 30
    return max(0, (date.today() - d).days)


def recovery_progress(day_since: int, window_days: int = 90) -> float:
    """0..1 sigmoid over the typical recovery window."""
    return 1 / (1 + math.exp(-0.08 * (day_since - window_days / 3)))


def simulate_tick(state: str, tick_seconds: int, progress: float) -> dict:
    """
    Generate increments for one tick.

    Returns {steps, distance_km, active_minutes, walk_speed, walk_cadence,
             walked_minutes}.  walk_speed/cadence are None unless the patient
             actually walked during this tick.
    """
    minutes = tick_seconds / 60.0

    out = {
        "steps": 0,
        "distance_km": 0.0,
        "active_minutes": 0.0,
        "walk_speed": None,
        "walk_cadence": None,
        "walked_minutes": 0.0,
    }

    if state == "sit":
        return out

    if state == "stand":
        out["steps"] = max(0, int(random.gauss(8, 4)))
        out["active_minutes"] = minutes
        out["distance_km"] = out["steps"] * 0.0007
        return out

    if state == "walk":
        # Spend a random fraction of the tick actually walking.
        walked = minutes * random.uniform(0.4, 0.9)
        cadence = max(30.0, random.gauss(50 + progress * 60, 5))   # spm
        speed = max(0.2, random.gauss(0.4 + progress * 0.9, 0.08))  # m/s
        steps = int(cadence * walked)

        out["steps"] = steps
        out["walked_minutes"] = walked
        out["walk_speed"] = round(speed, 2)
        out["walk_cadence"] = round(cadence, 1)
        out["active_minutes"] = minutes
        out["distance_km"] = round(steps * 0.0007, 3)
        return out

    if state == "exercise":
        # Light rehab: some marching/cycling, modest steps.
        cadence = max(40.0, random.gauss(60 + progress * 30, 6))
        speed = max(0.3, random.gauss(0.6 + progress * 0.4, 0.05))
        walked = minutes * random.uniform(0.3, 0.7)
        steps = int(cadence * walked * 0.6)

        out["steps"] = steps
        out["walked_minutes"] = walked
        out["walk_speed"] = round(speed, 2)
        out["walk_cadence"] = round(cadence, 1)
        out["active_minutes"] = minutes
        out["distance_km"] = round(steps * 0.0007, 3)
        return out

    return out


class DayAccumulator:
    """Running totals for the current day. Posts cumulative values to API."""

    def __init__(self, day: date):
        self.day = day
        self.steps = 0
        self.distance_km = 0.0
        self.active_minutes = 0.0
        self.walk_speed_sum = 0.0
        self.walk_cadence_sum = 0.0
        self.walk_minutes_total = 0.0

    def add(self, tick: dict) -> None:
        self.steps += tick["steps"]
        self.distance_km += tick["distance_km"]
        self.active_minutes += tick["active_minutes"]
        if tick["walk_speed"] is not None and tick["walked_minutes"] > 0:
            wm = tick["walked_minutes"]
            self.walk_speed_sum += tick["walk_speed"] * wm
            self.walk_cadence_sum += tick["walk_cadence"] * wm
            self.walk_minutes_total += wm

    def payload(self) -> dict:
        if self.walk_minutes_total > 0:
            avg_speed = round(self.walk_speed_sum / self.walk_minutes_total, 2)
            avg_cadence = round(self.walk_cadence_sum / self.walk_minutes_total, 1)
        else:
            avg_speed = 0.0
            avg_cadence = 0.0

        return {
            "record_date": self.day.isoformat(),
            "step_count": int(self.steps),
            "walking_speed": avg_speed,
            "cadence": avg_cadence,
            "distance": round(self.distance_km, 2),
            "active_minutes": int(self.active_minutes),
        }


def run_simulate(args: argparse.Namespace, token: str, base_url: str) -> int:
    try:
        profile = fetch_me(base_url, token)
    except urllib.error.HTTPError as e:
        print(f"[brain] /auth/me failed: {e.code} {e.read().decode()}", file=sys.stderr)
        return 1

    print(
        f"[brain] simulate mode  patient_id={profile.get('patient_id')}  "
        f"surgery_date={profile.get('surgery_date')}"
    )

    state = "sit"
    acc = DayAccumulator(date.today())

    while True:
        now = datetime.now()
        today = now.date()

        # Day rollover: post final cumulative for old day, reset.
        if today != acc.day:
            print(f"[brain] day rollover {acc.day} -> {today}")
            acc = DayAccumulator(today)

        progress = recovery_progress(days_since_surgery(profile))
        tick = simulate_tick(state, args.tick, progress)
        acc.add(tick)

        payload = acc.payload()
        try:
            saved = post_gait(base_url, token, payload)
            print(
                f"[brain] {now.strftime('%Y-%m-%d %H:%M')}  state={state:<8}  "
                f"+steps={tick['steps']:>4}  "
                f"day_total_steps={payload['step_count']:>5}  "
                f"avg_speed={payload['walking_speed']}m/s  "
                f"avg_cadence={payload['cadence']}  "
                f"dist={payload['distance']}km  "
                f"active={payload['active_minutes']}min  "
                f"-> id={saved.get('id')}"
            )
        except urllib.error.HTTPError as e:
            print(
                f"[brain] POST failed: {e.code} {e.read().decode()}",
                file=sys.stderr,
            )

        state = next_state(state)

        try:
            time.sleep(args.tick)
        except KeyboardInterrupt:
            print("\n[brain] interrupted, shutting down")
            return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


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

    if args.simulate:
        return run_simulate(args, token, args.base_url)

    today = date.today()

    if args.once or args.today:
        reading = simulate_reading(day_index=args.days - 1, total_days=args.days)
        reading["record_date"] = today.isoformat()
        return _send_one(args.base_url, token, today, reading)

    # Backfill mode
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
    p.add_argument(
        "--simulate",
        action="store_true",
        help="Long-running mode: tick every --tick seconds, accumulate into today's row",
    )
    p.add_argument(
        "--tick",
        type=int,
        default=1800,
        help="Seconds per simulate tick (default 1800 = 30 min)",
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
