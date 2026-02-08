import time
import json
import math
import random
import csv
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

BASE_URL = "http://alijomei.ir"
DRY_RUN = False

INTERVAL_SEC = 2
BATCH_COUNT = 5

GPS_CSV_PATH = "gps.csv"
OUT_FILE = "output.jsonl"


def iso_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def save(obj):
    with open(OUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def parse_iso(s: str) -> float:
    s = s.strip()
    if s.endswith("Z"):
        s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s).timestamp()


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def read_gps_csv(path: str):
    pts = []
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            ts = parse_iso(row["timestamp"])
            lat = float(row["lat"])
            lon = float(row["lon"])
            pts.append({"ts": ts, "lat": lat, "lon": lon})
    pts.sort(key=lambda x: x["ts"])
    if len(pts) < 2:
        raise ValueError("gps.csv باید حداقل 2 نقطه داشته باشد")
    return pts


def resample_to_interval(pts, interval_sec: int):
    out = [pts[0]]
    last_t = pts[0]["ts"]
    for p in pts[1:]:
        if p["ts"] - last_t >= interval_sec:
            out.append(p)
            last_t = p["ts"]
    if len(out) < 2:
        out = pts[:]
    return out


def add_speed_kph(pts):
    out = [pts[0].copy()]
    for i in range(1, len(pts)):
        a = pts[i - 1]
        b = pts[i]
        dt = max(1e-3, b["ts"] - a["ts"])
        dist = haversine_m(a["lat"], a["lon"], b["lat"], b["lon"])
        speed_kph = (dist / dt) * 3.6
        cur = b.copy()
        cur["speed_kph"] = float(speed_kph)
        out.append(cur)
    out[0]["speed_kph"] = out[1]["speed_kph"]
    return out


@dataclass
class SensorState:
    rpm: int
    coolant_c: float
    fuel_pct: float
    cabin_c: float
    seq: int = 0

    def step(self, speed_kph: float):
        rpm_target = clamp(800 + speed_kph * 30, 700, 4500)
        self.rpm = int(self.rpm + (rpm_target - self.rpm) * 0.35 + random.uniform(-50, 50))
        self.rpm = int(clamp(self.rpm, 700, 5000))

        coolant_target = 88 + clamp(speed_kph / 120, 0, 1) * 7
        self.coolant_c = round(
            clamp(self.coolant_c + (coolant_target - self.coolant_c) * 0.08 + random.uniform(-0.1, 0.1), 60, 110), 1
        )

        cabin_target = 22 + random.uniform(-1.5, 1.5)
        self.cabin_c = round(
            clamp(self.cabin_c + (cabin_target - self.cabin_c) * 0.05 + random.uniform(-0.05, 0.05), 10, 35), 1
        )

        self.fuel_pct = round(clamp(self.fuel_pct - random.uniform(0.01, 0.06), 0, 100), 1)


def start_session(client):
    payload = {"device_time": iso_now(), "session_metadata": []}
    save({"endpoint": "start", "payload": payload})

    if DRY_RUN:
        return "dry_run_session"

    r = client.post("/v1/sessions/start", json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()
    sid = data.get("session_id") if isinstance(data, dict) else data
    save({"endpoint": "start", "response": data})
    return sid


def send_batch(client, payload):
    save({"endpoint": "telemetry", "payload": payload})

    if DRY_RUN:
        return

    r = client.post("/v1/telemetry:batch", json=payload, timeout=20)
    r.raise_for_status()


def end_session(client, session_id):
    params = {"session_id": session_id, "device_time": iso_now()}
    save({"endpoint": "end", "payload": params})

    if DRY_RUN:
        return

    r = client.post("/v1/sessions/end", params=params, timeout=20)
    r.raise_for_status()


def build_batch(session_id, t_iso, gps_lat, gps_lon, speed_kph, sensors: SensorState):
    sensors.step(speed_kph)

    records = [
        {"seq": sensors.seq, "type": "gps", "device_time": t_iso,
         "data": {"lat": gps_lat, "lon": gps_lon, "speed_kph": round(speed_kph, 2)}},
        {"seq": sensors.seq + 1, "type": "obd", "device_time": t_iso,
         "data": {"rpm": sensors.rpm, "coolant_c": sensors.coolant_c, "fuel_pct": sensors.fuel_pct}},
        {"seq": sensors.seq + 2, "type": "temp", "device_time": t_iso,
         "data": {"cabin_c": sensors.cabin_c}},
    ]
    sensors.seq += 3
    return {"session_id": session_id, "records": records}


def main():
    print("START")

    pts = read_gps_csv(GPS_CSV_PATH)
    pts = resample_to_interval(pts, INTERVAL_SEC)
    pts = add_speed_kph(pts)

    sensors = SensorState(rpm=900, coolant_c=75.0, fuel_pct=70.0, cabin_c=22.0)

    with httpx.Client(base_url=BASE_URL) as client:
        session_id = start_session(client)

        sent = 0
        for p in pts:
            if sent >= BATCH_COUNT:
                break

            t_iso = datetime.fromtimestamp(p["ts"], tz=timezone.utc).isoformat().replace("+00:00", "Z")
            speed = clamp(p["speed_kph"], 0, 140)

            batch = build_batch(
                session_id=session_id,
                t_iso=t_iso,
                gps_lat=p["lat"],
                gps_lon=p["lon"],
                speed_kph=speed,
                sensors=sensors,
            )
            send_batch(client, batch)
            sent += 1
            time.sleep(INTERVAL_SEC)

        end_session(client, session_id)

    print("DONE")


if __name__ == "__main__":
    main()
