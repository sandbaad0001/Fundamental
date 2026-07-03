from app.core.database import SessionLocal
from app.models.models import Stock

class MarketCleaner:
    @staticmethod
    def categorize_market():
        """بررسی تک‌تک نمادها و تعیین نوع دقیق آن‌ها در فیلد sector"""
        print("در حال دسته‌بندی و تمیزکاری نمادهای بازار بورس...")
        db = SessionLocal()
        
        try:
            stocks = db.query(Stock).all()
            
            counters = {
                "سهام": 0,
                "صندوق سرمایه‌گذاری": 0,
                "اختیار معامله": 0,
                "اوراق بدهی": 0,
                "حق تقدم": 0
            }
            
            for stock in stocks:
                ticker = stock.ticker.strip()
                name = stock.name.strip()
                
                # ۱. الگوی تشخیص اختیار معامله (شروع با ض یا ط / وجود کلمه اختیار در نام)
                if ticker.startswith('ض') or ticker.startswith('ط') or 'اختیار' in name:
                    stock.sector = "اختیار معامله"
                    counters["اختیار معامله"] += 1
                    
                # ۲. الگوی تشخیص اوراق بدهی (اخزا، گام، مرابحه، صکوک)
                elif ticker.startswith('اخزا') or ticker.startswith('گام') or 'مرابحه' in name or 'مشارکت' in name:
                    stock.sector = "اوراق بدهی"
                    counters["اوراق بدهی"] += 1
                    
                # ۳. الگوی تشخیص صندوق‌های سرمایه‌گذاری
                elif 'صندوق' in name or 'ETF' in name or 'سرمایه گذاری مشترک' in name:
                    stock.sector = "صندوق سرمایه‌گذاری"
                    counters["صندوق سرمایه‌گذاری"] += 1
                    
                # ۴. الگوی تشخیص حق تقدم (انتهای نماد حرف ح باشد و طول نماد بیش از ۳ حرف باشد)
                elif ticker.endswith('ح') and len(ticker) > 3 and not ticker.startswith('ص'):
                    stock.sector = "حق تقدم"
                    counters["حق تقدم"] += 1
                    
                # ۵. در غیر این صورت، سهم عادی شرکت است
                else:
                    stock.sector = "سهام"
                    counters["سهام"] += 1
            
            db.commit()
            
            print("\n" + "="*40)
            print("📊 گزارش نهایی تفکیک بازار:")
            for category, count in counters.items():
                print(f"🔹 {category}: {count} نماد")
            print("="*40)
            
        except Exception as e:
            db.rollback()
            print(f"خطا در تمیزکاری دیتابیس: {e}")
        finally:
            db.close()