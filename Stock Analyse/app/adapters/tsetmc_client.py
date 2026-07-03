import time
import requests
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# خاموش کردن هشدارهای امنیتی مربوط به سایت‌های بدون https
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TsetmcAdapter:
    def __init__(self):
        # آدرس مستقیم و خام دیتای هسته قدیم که در هر ساعتی از شبانه‌روز اطلاعات دارد
        self.old_api_url = "http://old.tsetmc.com/tsev2/data/MarketWatchInit.aspx?h=0&r=0"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def get_all_stocks(self) -> list[dict]:
        print("🤖 در حال اجرای مکانیزم تهاجمی و استخراج مستقیم از هسته کلاسیک معاملات...")
        
        # گام اول: استفاده از کتابخانه سریع Requests (با دور زدن پروکسی‌های مزاحم ویندوز)
        try:
            session = requests.Session()
            session.trust_env = False  # نادیده گرفتن تمام VPN ها و تنظیمات شبکه
            headers = {"User-Agent": self.user_agent}
            
            response = session.get(self.old_api_url, headers=headers, timeout=15)
            
            if response.status_code == 200 and len(response.text) > 500:
                data = self._parse_old_api(response.text)
                if data:
                    print("✅ لیست نمادها با موفقیت در کسری از ثانیه (بدون مرورگر) دریافت شد.")
                    return data
        except Exception as e:
            print(f"⚠️ خطای موتور اول (شبکه محلی): {e}")

        # گام دوم: اگر موتور اول بلاک شد، مستقیماً با سلنیوم لینک خام را باز می‌کنیم (بدون خطای CORS)
        print("🤖 سوییچ به مرورگر هوشمند برای دور زدن فیلترینگ...")
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"user-agent={self.user_agent}")
            
            service = Service("./chromedriver.exe")
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # باز کردن مستقیم لینکِ متنی به جای صفحه اصلی بورس
            driver.get(self.old_api_url)
            time.sleep(4)
            
            # استخراج متن خام از تگ بدنه
            raw_text = driver.find_element(By.TAG_NAME, "body").text
            
            if raw_text and len(raw_text) > 500:
                print("✅ اتصال مرورگر به هسته کلاسیک موفقیت‌آمیز بود.")
                return self._parse_old_api(raw_text)
            else:
                print("❌ سرور بورس هیچ دیتایی برنگرداند.")
                return []
        except Exception as e:
            print(f"❌ خطای موتور مرورگر: {e}")
            return []
        finally:
            if driver:
                driver.quit()

    def _parse_old_api(self, raw_text: str) -> list[dict]:
        """پارس کردن رشته‌های متنیِ هسته قدیمی بورس به دیکشنری پایتون"""
        parsed_data = []
        try:
            # دیتای هسته قدیم با علامت @ از هم جدا شده‌اند (بخش سوم مربوط به نمادهاست)
            parts = raw_text.split('@')
            if len(parts) > 2:
                market_data = parts[2]
                stocks = market_data.split(';') # هر سهم با سمی‌کالن جدا شده
                
                for stock in stocks:
                    fields = stock.split(',')
                    # بررسی می‌کنیم که ردیف حتماً کامل باشد
                    if len(fields) >= 22:
                        ins_code = fields[0].strip()
                        ticker = fields[2].strip()
                        name = fields[3].strip()
                        
                        # در هسته قدیمی، تعداد کل سهام همیشه در ایندکس 21 قرار دارد
                        try:
                            total_shares = float(fields[21])
                        except (IndexError, ValueError):
                            # هوش مصنوعی پارسر: اگر سایت بورس ساختارش را عوض کرد، 
                            # به دنبال اولین عددِ بزرگِ میلیاردری در انتهای ردیف بگرد
                            total_shares = 0
                            for field in reversed(fields):
                                if field.isdigit() and len(field) > 7: 
                                    total_shares = float(field)
                                    break
                                
                        # فقط نمادهای معتبر را استخراج کن
                        if ticker and ins_code and total_shares > 0:
                            parsed_data.append({
                                "ticker": ticker,
                                "name": name,
                                "ins_code": ins_code,
                                "total_shares": total_shares
                            })
        except Exception as e:
            print(f"❌ خطا در تجزیه داده‌های خام: {e}")
            
        return parsed_data