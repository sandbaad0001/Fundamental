from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# مسیر ساخت دیتابیس در همان پوشه اصلی پروژه
SQLALCHEMY_DATABASE_URL = "sqlite:///./iran_bourse.db"

# راه‌اندازی موتور دیتابیس
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# ساخت کارخانه تولید نشست‌ها (Sessions) برای اتصال به دیتابیس
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# کلاس پایه برای مدل‌ها (این باید قبل از فراخوانی مدل‌ها ساخته شود)
Base = declarative_base()

def init_db():
    """ساخت جداول دیتابیس در صورت عدم وجود"""
    # ایمپورت مدل‌ها در داخل تابع انجام می‌شود تا از خطای Circular Import جلوگیری شود
    import app.models.models 
    
    # ساخت تمام جداول بر اساس مدل‌های ایمپورت شده
    Base.metadata.create_all(bind=engine)