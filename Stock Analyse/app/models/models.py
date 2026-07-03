from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True)
    name = Column(String)
    sector = Column(String)
    ins_code = Column(String, index=True)
    total_shares = Column(Float, default=0) 
    
    # فیلدهای جدید تحلیل بنیادی
    net_profit_margin = Column(Float, default=0.0) # حاشیه سود خالص
    forward_pe = Column(Float, default=0.0)        # پی بر ای آینده‌نگر

    # 🛡️ سیستم ثبت مُهر زمان (Timestamp) برای راستی‌آزمایی دیتا
    last_updated_unix = Column(Float, nullable=True, default=0.0)
    last_updated_jalali = Column(String, nullable=True, default="نامشخص")

    prices = relationship("PriceHistory", back_populates="stock")
    fundamental_reports = relationship("FundamentalReport", back_populates="stock")

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    date = Column(Date, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    last_price = Column(Float)
    volume = Column(Integer)
    value = Column(Integer)
    stock = relationship("Stock", back_populates="prices")

class FundamentalReport(Base):
    __tablename__ = "fundamental_reports"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    report_title = Column(String)
    monthly_sales = Column(Float, default=0.0)
    ytd_sales = Column(Float, default=0.0)
    stock = relationship("Stock", back_populates="fundamental_reports")