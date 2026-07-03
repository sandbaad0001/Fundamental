import requests
import pandas as pd
import io
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CodalAdapter:
    def __init__(self):
        self.search_url = "https://search.codal.ir/api/search/v2/q"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        # تنظیمات مرورگر مخفی (بدون باز شدن پنجره گرافیکی)
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--log-level=3")
        self.chrome_options.add_argument(f"user-agent={self.user_agent}")

    def get_latest_reports(self, ticker: str, page: int = 1):
        params = {"Symbol": ticker, "PageNumber": page}
        # هدرهای کامل‌تر برای تقلید رفتار مرورگر
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://codal.ir/",
            "Origin": "https://codal.ir",
            "X-Requested-With": "XMLHttpRequest"
        }
        try:
            # استفاده از یک تایم‌اوت طولانی‌تر
            response = requests.get(self.search_url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json().get("Letters", [])
            else:
                print(f"⚠️ کد وضعیت کدال: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ خطای اتصال به سرور جستجوی کدال: {e}")
            return []

    def get_report_tables(self, url_suffix: str) -> list[pd.DataFrame]:
        """استخراج جداول پویای کدال با استفاده از مرورگر هوشمند سلنیوم"""
        full_url = f"https://codal.ir{url_suffix}"
        print(f"🌐 لینک گزارش: {full_url}")
        print("🤖 در حال راه‌اندازی مرورگر هوشمند سلنیوم (این مرحله حدود ۱۰ تا ۲۰ ثانیه زمان می‌برد)...")
        
        driver = None
        try:
            # به جای دانلود خودکار، مستقیماً به فایل دانلودی خودمان اشاره می‌کنیم
            service = Service("./chromedriver.exe")
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            # باز کردن سایت کدال
            driver.get(full_url)
            
            # صبر کردن تا زمانی که جداول توسط جاوا اسکریپت کدال در صفحه ظاهر شوند
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                time.sleep(3) # تاخیر برای اطمینان از تزریق اعداد
            except Exception:
                print("⚠️ زمان انتظار برای لود جداول تمام شد.")
            
            # دریافت سورس نهایی صفحه
            final_html = driver.page_source

            # سپردن سورس کامل به جراح HTML
            soup = BeautifulSoup(final_html, 'html.parser')
            html_tables = soup.find_all('table')
            
            if not html_tables:
                print("⚠️ مرورگر نامرئی هم نتوانست جدولی پیدا کند.")
                return []
                
            parsed_tables = []
            
            for table in html_tables:
                try:
                    table_str = str(table)
                    if len(table_str) < 500:
                        continue
                        
                    table_io = io.StringIO(table_str)
                    df_list = pd.read_html(table_io)
                    
                    if df_list and not df_list[0].empty:
                        parsed_tables.extend(df_list)
                except Exception:
                    continue
                    
            return parsed_tables

        except Exception as e:
            print(f"❌ خطای استخراج جداول با مرورگر هوشمند: {e}")
            return []
        finally:
            if driver:
                driver.quit()