"""
پاک کردن و ساخت مجدد جداول دیتابیس (بدون مایگریشن).
از ریشه پروژه اجرا کنید: python -m scripts.reset_db
"""
import os
import sys
from pathlib import Path

# مسیر rest_api_gateway برای import مدل‌ها
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root / "rest_api_gateway"))

from sqlalchemy import create_engine

from models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://api:api@localhost:5432/api")

def main():
    engine = create_engine(DATABASE_URL)
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Done. Database reset.")

if __name__ == "__main__":
    main()
