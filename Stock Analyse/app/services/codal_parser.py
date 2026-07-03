import pandas as pd
import re

class CodalParser:
    @staticmethod
    def _to_english_numbers(text: str) -> str:
        persian = '۰۱۲۳۴۵۶۷۸۹'
        arabic = '٠١٢٣٤٥٦٧٨٩'
        english = '0123456789'
        text = str(text)
        for p, e in zip(persian, english):
            text = text.replace(p, e)
        for a, e in zip(arabic, english):
            text = text.replace(a, e)
        return text

    @staticmethod
    def _extract_best_number(row_list: list) -> float:
        for cell in row_list:
            cell_str = str(cell)
            if not cell_str or cell_str.isspace():
                continue
            clean_cell = CodalParser._to_english_numbers(cell_str)
            is_negative = '(' in clean_cell
            digits = re.sub(r'[^\d.]', '', clean_cell)
            if digits:
                try:
                    val = float(digits)
                    if is_negative:
                        val = -val
                    if abs(val) > 1000:
                        return val
                except ValueError:
                    continue
        return 0.0

    @staticmethod
    def parse_monthly_report(tables: list[pd.DataFrame]) -> dict:
        if not tables: return None
        df = tables[0].copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(map(str, col)).strip() for col in df.columns]
        df = df.fillna('')
        
        total_row = None
        for _, row in df.iterrows():
            row_text = str(row.values).replace('\u200c', ' ')
            
            # الگو ۱: شرکت‌های تولیدی و صنعتی
            if 'جمع' in row_text and 'داخلی' not in row_text and 'صادراتی' not in row_text and 'سپرده' not in row_text and 'تسهیلات' not in row_text:
                total_row = row
            # الگو ۲: گروه بانک‌ها (مثل ونوین) - شکار درآمد تسهیلات
            elif 'جمع' in row_text and 'تسهیلات' in row_text and 'اعطایی' in row_text:
                total_row = row

        result = {"monthly_sales": 0.0, "ytd_sales": 0.0}
        if total_row is not None:
            for col_name, val in zip(df.columns, total_row.values):
                val_clean = CodalParser._to_english_numbers(str(val).strip()).replace(',', '').replace('/', '.')
                if val_clean and val_clean != '0':
                    try:
                        num = float(val_clean)
                        if num > 0:
                            if 'دوره یک ماهه' in col_name:
                                result['monthly_sales'] = num
                            elif 'از ابتدای سال مالی' in col_name and 'اصلاح شده' not in col_name:
                                if num > result['ytd_sales']:
                                    result['ytd_sales'] = num
                    except ValueError:
                        pass
        return result

    @staticmethod
    def parse_financial_statement(tables: list[pd.DataFrame]) -> float:
        if not tables: return 0.0
        
        revenue = 0.0
        net_profit = 0.0
        
        for df in tables:
            df = df.fillna('')
            for _, row in df.iterrows():
                row_list = [str(x) for x in row.values]
                raw_text = "".join(row_list).replace('\u200c', '').replace('ي', 'ی').replace('ك', 'ک')
                row_text_nospace = re.sub(r'\s+', '', raw_text)
                
                # شکار درآمدهای عملیاتی (پشتیبانی همزمان از صنعت و بانک)
                if revenue == 0.0 and any(k in row_text_nospace for k in ["درآمدهایعملیاتی", "درآمدعملیاتی", "فروشخالص", "خالصدرآمدهایتسهیلات", "جمعدرآمدهایعملیاتی"]):
                    revenue = CodalParser._extract_best_number(row_list)
                            
                # شکار سود خالص
                is_net_profit = ("سود" in row_text_nospace or "زیان" in row_text_nospace) and "خالص" in row_text_nospace
                is_not_eps = all(ex not in row_text_nospace for ex in ["سهم", "جامع", "انباشته", "پایه", "تقلیل", "قبل"])
                
                if net_profit == 0.0 and is_net_profit and is_not_eps:
                    net_profit = CodalParser._extract_best_number(row_list)
            
            if revenue != 0.0 and net_profit != 0.0:
                break
                
        if revenue > 0:
            margin = net_profit / revenue
            return round(margin, 4)
            
        return 0.0