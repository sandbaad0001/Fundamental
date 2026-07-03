import pandas as pd
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from app.core.database import SessionLocal
from app.models.models import Stock, PriceHistory

class TechnicalEngine:
    @staticmethod
    def get_stock_dataframe(ticker: str) -> pd.DataFrame:
        """دریافت تاریخچه قیمت یک نماد از دیتابیس و تبدیل به DataFrame"""
        db = SessionLocal()
        try:
            stock = db.query(Stock).filter(Stock.ticker == ticker).first()
            if not stock:
                return pd.DataFrame()
            
            prices = db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock.id
            ).order_by(PriceHistory.date.asc()).all()
            
            if not prices:
                return pd.DataFrame()
            
            data = [{
                "date": p.date,
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume
            } for p in prices]
            
            df = pd.DataFrame(data)
            df.set_index("date", inplace=True)
            return df
        finally:
            db.close()

    @classmethod
    def calculate_indicators(cls, ticker: str) -> pd.DataFrame:
        """محاسبه اندیکاتورهای تکنیکال با استفاده از کتابخانه ta"""
        df = cls.get_stock_dataframe(ticker)
        if df.empty:
            return df
            
        # ۱. محاسبه RSI (دوره ۱۴ روزه)
        df['RSI_14'] = RSIIndicator(close=df['close'], window=14).rsi()
        
        # ۲. محاسبه میانگین‌های متحرک
        df['SMA_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
        df['SMA_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
        
        # ۳. محاسبه MACD (سریع ۱۲، کند ۲۶، سیگنال ۹)
        macd = MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9)
        df['MACD_12_26_9'] = macd.macd()
        df['MACDs_12_26_9'] = macd.macd_signal()
        df['MACDh_12_26_9'] = macd.macd_diff()
        
        return df