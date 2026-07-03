import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

class ChartEngine:
    @staticmethod
    def plot_stock_dashboard(df: pd.DataFrame, ticker: str):
        """رسم نمودار شمعی متصل به اندیکاتورهای هوشمند تکنیکال"""
        if df.empty:
            print("❌ دیتافریم خالی است و امکان رسم نمودار وجود ندارد.")
            return

        df_plot = df.tail(100)

        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05,
            row_width=[0.2, 0.2, 0.6]
        )

        # --- ردیف ۱: نمودار کندل استیک ---
        fig.add_trace(
            go.Candlestick(
                x=df_plot.index,
                open=df_plot['open'], high=df_plot['high'],
                low=df_plot['low'], close=df_plot['close'],
                name="کندل قیمت"
            ),
            row=1, col=1
        )
        
        if 'SMA_20' in df_plot.columns:
            fig.add_trace(
                go.Scatter(x=df_plot.index, y=df_plot['SMA_20'], line=dict(color='orange', width=1.5), name='SMA 20'),
                row=1, col=1
            )

        # --- ردیف ۲: اندیکاتور MACD ---
        if 'MACD_12_26_9' in df_plot.columns:
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MACD_12_26_9'], line=dict(color='blue', width=1.5), name='MACD'), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MACDs_12_26_9'], line=dict(color='red', width=1), name='Signal'), row=2, col=1)
            fig.add_trace(go.Bar(x=df_plot.index, y=df_plot['MACDh_12_26_9'], name='Histogram', marker_color='gray'), row=2, col=1)

        # --- ردیف ۳: اندیکاتور RSI ---
        if 'RSI_14' in df_plot.columns:
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['RSI_14'], line=dict(color='purple', width=1.5), name='RSI 14'), row=3, col=1)
            fig.add_shape(type="line", x0=df_plot.index[0], y0=70, x1=df_plot.index[-1], y1=70, line=dict(color="red", dash="dash"), row=3, col=1)
            fig.add_shape(type="line", x0=df_plot.index[0], y0=30, x1=df_plot.index[-1], y1=30, line=dict(color="green", dash="dash"), row=3, col=1)

        fig.update_layout(
            title=f"داشبورد تحلیل تکنیکال نماد {ticker}",
            yaxis_title="قیمت (ریال)",
            yaxis2_title="MACD",
            yaxis3_title="RSI",
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            height=800
        )

        # --- تغییر اصلی اینجاست ---
        # به جای fig.show() نمودار را در یک فایل HTML ذخیره و مستقیماً باز می‌کنیم
        html_file = f"{ticker}_chart.html"
        fig.write_html(html_file, auto_open=True)
        print(f"✅ نمودار با موفقیت ساخته شد و در مرورگر باز شد (فایل: {html_file})")