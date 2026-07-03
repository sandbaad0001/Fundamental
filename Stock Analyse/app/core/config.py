import os

class Settings:
    # آدرس پیش‌فرض دیتابیس. 
    # الان روی SQLite تنظیم شده تا یک فایل به نام iran_bourse.db در پوشه اصلی بسازد.
    # برای نسخه نهایی، فقط کافیست این مقدار را به آدرس سرور PostgreSQL تغییر دهید.
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./iran_bourse.db")

settings = Settings()