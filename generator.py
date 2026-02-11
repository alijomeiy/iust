#!/usr/bin/env python3
"""
Telemetry Generator (only cars + days, Finglish prompts)
Now also sends:
- /v1/sessions/start  -> queue: session_events
- /v1/device/heartbeat -> queue: device_heartbeat
- /v1/sessions/end    -> queue: session_events

Also writes local summary file: run_summary.json
"""

from __future__ import annotations

import json
import math
import random
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

import requests


IRAN_CITIES: List[Tuple[str, float, float]] = [
    ("Tehran", 35.6892, 51.3890),
    ("Shiraz", 29.5918, 52.5837),
    ("Isfahan", 32.6546, 51.6680),
    ("Mashhad", 36.2605, 59.6168),
    ("Tabriz", 38.0962, 46.2738),
    ("Ahvaz", 31.3183, 48.6706),
    ("Rasht", 37.2808, 49.5832),
    ("Kerman", 30.2839, 57.0834),
    ("Yazd", 31.8974, 54.3569),
    ("Qom", 34.6416, 50.8746),
]


@dataclass
class CarProfile:
    car_id: str
    home_city: str
    home_lat: float
    home_lon: float
    daily_km_mean: float
    daily_km_std: float
    travel_city: Tuple[str, float, float] | None


@dataclass
class CarRunSummary:
    car_id: str
    session_id: str
    dominant_city: str
    days_requested: int
    active_days: int
    total_km_approx: int
    trips_total: int
    batches_sent: int
    heartbeats_sent: int
    has_travel_city: bool


def read_int(prompt: str, min_v: int, max_v: int) -> int:
    while True:
        s = input(prompt).strip()
        try:
            v = int(s)
        except ValueError:
            print("Adad sahih vared kon.")
            continue
        if v < min_v or v > max_v:
            print(f"Bayad beyn {min_v} ta {max_v} bashe.")
            continue
        return v


def iso_z(dt: datetime) -> str:
    dt_utc = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt_utc.isoformat().replace("+00:00", "Z")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def random_point_near(lat: float, lon: float, radius_km: float) -> Tuple[float, float]:
    dlat = (radius_km / 111.0) * random.uniform(-1, 1)
    dlon = (radius_km / (111.0 * max(0.2, math.cos(math.radians(lat))))) * random.uniform(-1, 1)
    return lat + dlat, lon + dlon


def make_profile(i: int, days: int) -> CarProfile:
    home_city, home_lat, home_lon = random.choice(IRAN_CITIES)

    base = 22 + min(55, days * 0.8)
    daily_mean = random.uniform(base * 0.6, base * 1.1)
    daily_std = daily_mean * random.uniform(0.25, 0.45)

    travel_city = None
    if random.random() < 0.35:
        travel_city = random.choice([c for c in IRAN_CITIES if c[0] != home_city])

    return CarProfile(
        car_id=f"car-{i:03d}",
        home_city=home_city,
        home_lat=home_lat,
        home_lon=home_lon,
        daily_km_mean=daily_mean,
        daily_km_std=daily_std,
        travel_city=travel_city,
    )


def daily_km(profile: CarProfile) -> float:
    # some rest days
    if random.random() < 0.08:
        return 0.0
    km = random.gauss(profile.daily_km_mean, profile.daily_km_std)
    return max(2.0, min(km, profile.daily_km_mean * 2.2))


def generate_trip_points(start_lat: float, start_lon: float, trip_km: float, points: int) -> List[Tuple[float, float]]:
    points = max(2, points)
    pts = [(start_lat, start_lon)]
    remaining = trip_km
    lat, lon = start_lat, start_lon

    for _ in range(points - 1):
        if remaining <= 0:
            lat2, lon2 = random_point_near(lat, lon, radius_km=0.2)
        else:
            step_km = remaining / max(1, (points - len(pts)))
            step_km = max(0.3, min(step_km, 5.0))
            bearing = random.uniform(0, 2 * math.pi)
            dlat = (step_km * math.cos(bearing)) / 111.0
            dlon = (step_km * math.sin(bearing)) / (111.0 * max(0.2, math.cos(math.radians(lat))))
            lat2, lon2 = lat + dlat, lon + dlon

        d = haversine_km(lat, lon, lat2, lon2)
        remaining -= d
        lat, lon = lat2, lon2
        pts.append((lat, lon))

    return pts


# ---- API calls ----

def post_json(api_base: str, path: str, payload: Dict[str, Any], timeout_s: int = 20) -> Dict[str, Any]:
    url = api_base.rstrip("/") + path
    r = requests.post(url, json=payload, timeout=timeout_s)
    if r.status_code >= 300:
        raise RuntimeError(f"POST {path} failed: {r.status_code} {r.text}")
    try:
        return r.json()
    except Exception:
        return {"raw": r.text}


def start_session(api_base: str, car_id: str, now_dt: datetime, dominant_city: str) -> str:
    payload = {
        "device_id": car_id,
        "device_time": iso_z(now_dt),
        "metadata": [{"key": "dominant_city", "value": dominant_city}],
    }
    res = post_json(api_base, "/v1/sessions/start", payload)
    sid = res.get("session_id")
    if not sid:
        raise RuntimeError(f"start_session: no session_id in response: {res}")
    return str(sid)


def end_session(api_base: str, session_id: str, car_id: str, now_dt: datetime) -> None:
    # session_id and device_time must be sent as QUERY params (based on 422 error)
    params = {
        "session_id": session_id,
        "device_time": iso_z(now_dt),
    }
    url = api_base.rstrip("/") + "/v1/sessions/end"
    r = requests.post(url, params=params, json={"device_id": car_id}, timeout=20)
    if r.status_code >= 300:
        raise RuntimeError(f"POST /v1/sessions/end failed: {r.status_code} {r.text}")



def send_heartbeat(api_base: str, car_id: str, now_dt: datetime) -> None:
    payload = {
        "device_id": car_id,
        "device_time": iso_z(now_dt),

        "battery_pct": random.randint(35, 100),
        "storage_free_mb": random.randint(500, 50000),

        # must be dict
        "network": {
            "type": random.choice(["wifi", "lte", "3g", "offline"]),
            "signal": random.randint(0, 5),
        },

        # must be dict
        "camera": {
            "status": random.choice(["ok", "blocked", "error"]),
            "fps": random.choice([0, 15, 30]),
        },
    }
    post_json(api_base, "/v1/device/heartbeat", payload)




def send_telemetry_batch(api_base: str, session_id: str, car_id: str, records: List[Dict[str, Any]]) -> None:
    payload = {"session_id": session_id, "device_id": car_id, "records": records}
    post_json(api_base, "/v1/telemetry:batch", payload)


def main() -> int:
    print("\n=== Telemetry Generator ===\n")
    api_base = "http://localhost:8000"

    cars = read_int("Tedad mashin: ", 1, 500)
    days = read_int("Chand rooz: ", 1, 365)

    start_dt = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0)

    print("\nSending events + telemetry + heartbeats...\n")

    run_summaries: List[CarRunSummary] = []
    total_batches = 0

    for i in range(1, cars + 1):
        prof = make_profile(i, days)

        # 1) start session (goes to session_events queue)
        session_id = start_session(api_base, prof.car_id, start_dt, prof.home_city)

        car_total_km = 0.0
        car_batches = 0
        car_trips_total = 0
        hb_sent = 0
        active_days = 0

        travel_block = None
        if prof.travel_city and days >= 10 and random.random() < 0.7:
            block_len = random.randint(3, min(10, days))
            start_day = random.randint(0, days - block_len)
            travel_block = (start_day, start_day + block_len)

        seq = 0
        last_time = start_dt

        for d in range(days):
            day_km = daily_km(prof)
            if day_km <= 0:
                continue

            active_days += 1

            if travel_block and travel_block[0] <= d < travel_block[1]:
                city_name, city_lat, city_lon = prof.travel_city  # type: ignore[misc]
            else:
                city_name, city_lat, city_lon = prof.home_city, prof.home_lat, prof.home_lon

            # random daily trips & points
            trips = random.randint(1, 6)
            points_per_trip = random.randint(12, 35)

            weights = [random.random() for _ in range(trips)]
            s = sum(weights)
            trip_kms = [day_km * (w / s) for w in weights]

            day_start = start_dt + timedelta(days=d, hours=random.randint(0, 3))
            t_cursor = day_start

            records: List[Dict[str, Any]] = []
            for trip_km in trip_kms:
                start_lat, start_lon = random_point_near(city_lat, city_lon, radius_km=2.0)
                pts = generate_trip_points(start_lat, start_lon, trip_km=trip_km, points=points_per_trip)

                avg_speed = random.uniform(20.0, 55.0)
                trip_hours = max(0.08, trip_km / avg_speed)
                trip_seconds = int(trip_hours * 3600)
                gap_seconds = random.randint(5 * 60, 60 * 60)

                step_sec = max(5, trip_seconds // (len(pts) - 1))

                for (lat, lon) in pts:
                    seq += 1
                    speed = max(0.0, min(random.gauss(avg_speed, avg_speed * 0.25), 110.0))
                    records.append(
                        {
                            "seq": seq,
                            "type": "gps",
                            "device_time": iso_z(t_cursor),
                            "data": {
                                "lat": round(lat, 6),
                                "lon": round(lon, 6),
                                "speed": round(speed, 2),
                                "city": city_name,
                            },
                        }
                    )
                    t_cursor += timedelta(seconds=step_sec)

                t_cursor += timedelta(seconds=gap_seconds)
                car_total_km += trip_km

            car_trips_total += trips
            last_time = t_cursor

            # 2) send telemetry batch (goes to telemetry_batch queue)
            send_telemetry_batch(api_base, session_id, prof.car_id, records)
            car_batches += 1
            total_batches += 1

            # 3) send heartbeat sometimes (goes to device_heartbeat queue)
            if random.random() < 0.35:
                send_heartbeat(api_base, prof.car_id, t_cursor)
                hb_sent += 1

            time.sleep(0.02)

        # always send one final heartbeat at end (to guarantee queue isn't empty)
        send_heartbeat(api_base, prof.car_id, last_time)
        hb_sent += 1

        # 4) end session (goes to session_events queue)
        end_session(api_base, session_id, prof.car_id, last_time)

        run_summaries.append(
            CarRunSummary(
                car_id=prof.car_id,
                session_id=session_id,
                dominant_city=prof.home_city,
                days_requested=days,
                active_days=active_days,
                total_km_approx=int(round(car_total_km)),
                trips_total=car_trips_total,
                batches_sent=car_batches,
                heartbeats_sent=hb_sent,
                has_travel_city=bool(prof.travel_city),
            )
        )

    # Write JSON summary
    out = {
        "generated_at": iso_z(datetime.now(timezone.utc)),
        "api_base": api_base,
        "cars": cars,
        "days": days,
        "cars_summary": [asdict(x) for x in run_summaries],
    }
    with open("run_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # Print summary
    print("=== Summary ===")
    for s in run_summaries:
        travel_txt = " + travel" if s.has_travel_city else ""
        print(
            f"{s.car_id}: city={s.dominant_city}{travel_txt} | days={days} | "
            f"active_days={s.active_days} | ~{s.total_km_approx}km | "
            f"trips={s.trips_total} | batches={s.batches_sent} | heartbeats={s.heartbeats_sent}"
        )

    print(f"\nTotal telemetry batches sent: {total_batches}")
    print("Saved: run_summary.json")
    print("Done.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
