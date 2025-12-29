from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DATABASE_URL = "postgresql://api:api@192.168.21.81:5432/api"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ایجاد جداول در دیتابیس (در صورت نیاز)
Base.metadata.create_all(bind=engine)
