import csv
from datetime import datetime, timezone

PLT_PATH = r"C:\Users\ZAITOON.iR\Desktop\data\Geolife Trajectories 1.3\Data\000\Trajectory\20081023025304.plt"
OUT_CSV = "gps.csv"

def to_iso_z(date_str: str, time_str: str) -> str:
    
    dt = datetime.fromisoformat(f"{date_str}T{time_str}")
    return dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

def main():
    with open(PLT_PATH, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()

   
    data_lines = lines[6:]

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as out:
        w = csv.DictWriter(out, fieldnames=["timestamp", "lat", "lon"])
        w.writeheader()

        for line in data_lines:
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 7:
                continue

            
            lat = float(parts[0])
            lon = float(parts[1])
            date_str = parts[5]
            time_str = parts[6]
            ts = to_iso_z(date_str, time_str)

            w.writerow({"timestamp": ts, "lat": lat, "lon": lon})

    print("Wrote:", OUT_CSV)

if __name__ == "__main__":
    main()
