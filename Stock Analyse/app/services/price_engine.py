from datetime import datetime
from app.core.database import SessionLocal
from app.models.models import Stock, PriceHistory
from app.adapters.tsetmc_client import TSETMCAdapter

class PriceEngine:
    @staticmethod
    def sync_market_history(limit_count: int = 5):
        """دریافت و بروزرسانی تاریخچه قیمت سهام"""
        print(f"🚀 موتور تاریخچه قیمت روشن شد. در حال پردازش {limit_count} نماد اول سهام...")
        
        db = SessionLocal()
        tsetmc = TSETMCAdapter()
        
        try:
            # فقط نمادهایی را انتخاب می‌کنیم که در فاز قبل به عنوان «سهام» شناسایی شدند و InsCode دارند
            active_stocks = db.query(Stock).filter(
                Stock.sector == "سهام",
                Stock.ins_code != None
            ).limit(limit_count).all()
            
            for stock in active_stocks:
                print(f"📥 در حال دانلود تاریخچه قیمتی نماد: {stock.ticker} ...")
                history_data = tsetmc.fetch_price_history(stock.ins_code)
                
                price_records = []
                for day in history_data:
                    # سرور بورس تاریخ را در فیلد dEven برمی‌گرداند (مثلاً 20240101)
                    date_val = day.get("dEven")
                    if not date_val:
                        continue
                        
                    date_str = str(date_val)
                    try:
                        date_obj = datetime.strptime(date_str, "%Y%m%d").date()
                    except ValueError:
                        continue
                    
                    # بررسی عدم وجود داده تکراری برای این روز خاص
                    existing_price = db.query(PriceHistory).filter(
                        PriceHistory.stock_id == stock.id,
                        PriceHistory.date == date_obj
                    ).first()
                    
                    if not existing_price:
                        # ساخت رکورد قیمت روزانه
                        price_record = PriceHistory(
                            stock_id=stock.id,
                            date=date_obj,
                            open=float(day.get("priceFirst", 0)),
                            high=float(day.get("priceMax", 0)),
                            low=float(day.get("priceMin", 0)),
                            close=float(day.get("pClosing", 0)),     # قیمت پایانی
                            last_price=float(day.get("pDrMin", 0)),  # آخرین معامله
                            volume=int(day.get("qTitMeZVu", 0)),     # حجم معاملات
                            value=int(day.get("pMeZVu", 0))          # ارزش معاملات
                        )
                        price_records.append(price_record)
                
                if price_records:
                    db.bulk_save_objects(price_records)
                    db.commit()
                    print(f"✨ تعداد {len(price_records)} روز معاملاتی برای {stock.ticker} ذخیره شد.")
                else:
                    print(f"⚠️ دیتای جدیدی برای ذخیره در نماد {stock.ticker} یافت نشد (یا قبلاً ذخیره شده است).")
            
            print("\n✅ عملیات همگام‌سازی تاریخچه قیمت‌ها با موفقیت پایان یافت.")
            
        except Exception as e:
            db.rollback()
            print(f"❌ خطا در اجرای موتور قیمتی: {e}")
        finally:
            db.close()