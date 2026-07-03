import sys
import io
import time
import jdatetime
import requests
import urllib3
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# خاموش کردن هشدارهای امنیتی کانکشن‌های ایران
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.core.database import SessionLocal
from app.models.models import Stock, FundamentalReport
from app.adapters.codal_client import CodalAdapter
from app.services.codal_parser import CodalParser

def get_live_price(ins_code: str) -> float:
    """موتور دوگانه و ضدتحریم برای دریافت قیمت لحظه‌ای"""
    session = requests.Session()
    session.trust_env = False  # نادیده گرفتن پروکسی‌ها و VPNهای ویندوز
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # موتور اول: اتصال به API مدرن سایت بورس
    try:
        url_json = f"https://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDaily/{ins_code}"
        response = session.get(url_json, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            data = response.json()
            if "closingPriceDaily" in data and data["closingPriceDaily"]:
                price = float(data["closingPriceDaily"].get("pClosing", 0)) # قیمت پایانی
                if price > 0: 
                    return price
    except:
        pass
        
    # موتور دوم: در صورت قطع بودن API جدید، سوییچ به هسته کلاسیک
    try:
        url_old = f"http://old.tsetmc.com/tsev2/data/instinfofast.aspx?i={ins_code}&c=1"
        response = session.get(url_old, headers=headers, timeout=10)
        if response.status_code == 200:
            parts = response.text.split(',')
            if len(parts) >= 4:
                price = float(parts[3]) # قیمت پایانی
                if price > 0: 
                    return price
    except:
        pass
        
    return 0.0

def extract_income_statement_with_ai(url: str) -> float:
    if not url.startswith("http"):
        url = "https://codal.ir" + (url if url.startswith("/") else "/" + url)

    print(f"   🌐 لینک پردازش: {url}")
    print("   🤖 فعال‌سازی بینایی ماشین برای جستجو و کلیک روی تب 'سود و زیان'...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3")

    driver = None
    try:
        service = Service("./chromedriver.exe")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(url)
        time.sleep(3) 

        tabs = driver.find_elements(By.XPATH, "//a[contains(., 'سود') and contains(., 'زیان')]")
        tab_clicked = False

        for tab in tabs:
            if tab.is_displayed():
                if "تلفیقی" not in tab.text:
                    driver.execute_script("arguments[0].click();", tab)
                    tab_clicked = True
                    time.sleep(5) 
                    break

        if not tab_clicked and len(tabs) > 0:
            driver.execute_script("arguments[0].click();", tabs[0])
            time.sleep(5)

        html = driver.page_source
        tables = pd.read_html(io.StringIO(html))
        
        return CodalParser.parse_financial_statement(tables)

    except Exception as e:
        print(f"   ❌ خطای بینایی ماشین: {e}")
        return 0.0
    finally:
        if driver:
            driver.quit()

def run_fully_automated_analysis(target_tickers: list[str]):
    print("\n" + "═"*80)
    print(" 🧠 سیستم تحلیل‌گر تمام‌خودکار GARP (پیش‌بینی P/E تحلیلی)")
    print("═"*80)

    codal = CodalAdapter()
    db = SessionLocal()
    results = []

    try:
        for ticker in target_tickers:
            print(f"\n⏳ در حال پردازش فوق‌عمیق [{ticker}] ...")
            clean_ticker = ticker.replace('ي', 'ی').replace('ك', 'ک')
            stock = db.query(Stock).filter(Stock.ticker == clean_ticker).first()
            
            if not stock or stock.total_shares == 0:
                print(f"   ⚠️ اطلاعات پایه سهم در دیتابیس یافت نشد.")
                continue

            report = db.query(FundamentalReport).filter(
                FundamentalReport.stock_id == stock.id
            ).order_by(FundamentalReport.id.desc()).first()
            
            if not report or report.monthly_sales == 0:
                print(f"   ⚠️ گزارش فروش ماهانه یافت نشد.")
                continue
                
            print("   🌐 استخراج صورت‌های مالی فصلی از کدال...")
            reports = codal.get_latest_reports(clean_ticker)
            financial_report = next((r for r in reports if "صورت‌های مالی" in r.get("Title", "") and "حسابرسی نشده" in r.get("Title", "")), None)
            
            margin = 0.0
            if financial_report:
                url = financial_report.get('Url')
                margin = extract_income_statement_with_ai(url)
                
                if margin > 0:
                    stock.net_profit_margin = margin
                    db.commit()
                    print(f"   📊 حاشیه سود خالص استخراج شد: {margin*100:.1f}%")
                else:
                    print("   ⚠️ حاشیه سود استخراج نشد.")
                    continue
            else:
                print("   ⚠️ صورت مالی مناسبی یافت نشد.")
                continue

            print("   📡 دریافت قیمت زنده از هسته معاملات...")
            live_price = get_live_price(stock.ins_code)
            if live_price == 0:
                print("   ⚠️ خطا در دریافت قیمت لحظه‌ای.")
                continue
            print(f"   ✅ قیمت پایانی دریافت شد: {live_price:,.0f} ریال")

            # === موتور محاسبات کوانت (شبیه‌ساز ذهن تحلیلگر بنیادی) ===
            annualized_sales = report.monthly_sales * 12
            projected_net_profit = annualized_sales * margin
            projected_net_profit_rial = projected_net_profit * 1_000_000 
            
            forward_eps = projected_net_profit_rial / stock.total_shares
            forward_pe = live_price / forward_eps

            stock.forward_pe = forward_pe
            
            # 🛡️ سیستم ثبت مُهر زمان (Timestamp)
            # این دو خط، تاریخ دقیق استخراج دیتا را در دیتابیس ثبت می‌کنند
            stock.last_updated_unix = time.time()
            stock.last_updated_jalali = jdatetime.datetime.now().strftime("%Y/%m/%d - %H:%M")
            
            db.commit()

            results.append({
                "ticker": ticker,
                "price": live_price,
                "margin": margin,
                "eps": forward_eps,
                "pe": forward_pe
            })

    finally:
        db.close()

    # رندرینگ داشبورد نهایی (Noir Terminal Style)
    print("\n\n" + "═"*80)
    print(f" 💎 داشبورد ارزش‌گذاری سهام (بر اساس متد GARP) ".center(75))
    print("═"*80)
    print(f" {'نماد':<12} | {'قیمت زنده(ریال)':<18} | {'حاشیه سود':<12} | {'EPS تحلیلی':<15} | {'Forward P/E':<10}")
    print("─"*80)
    
    # مرتب‌سازی: جذاب‌ترین P/E (کمترین عدد) در صدر جدول قرار می‌گیرد
    results.sort(key=lambda x: x['pe'])
    
    for r in results:
        print(f" {r['ticker']:<12} | {r['price']:<18,.0f} | {r['margin']*100:>9.1f}%   | {r['eps']:<15,.0f} | {r['pe']:<10.2f}")
    
    print("═"*80 + "\n")

if __name__ == "__main__":
    # شما می‌توانید هر نمادی را به این لیست اضافه کنید!
    my_watchlist = ["ونوین", "فملی", "شپدیس"]
    run_fully_automated_analysis(my_watchlist)