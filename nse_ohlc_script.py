import pandas as pd
import yfinance as yf
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import os
import time


# ================= GET F&O SYMBOLS =================
def get_symbols():
    url = "https://www.nseindia.com/api/market-data-pre-open?key=FO"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.nseindia.com/"
    }

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)

    response = session.get(url, headers=headers, timeout=10)
    data_json = response.json()

    symbols = []

    for item in data_json["data"]:
        try:
            symbol = item["metadata"]["symbol"]
            final_val = item["detail"]["preOpenMarket"]["finalPrice"]

            # optional strong filter
            if float(final_val).is_integer():
                symbols.append(symbol + ".NS")
        except:
            continue

    return symbols


# ================= MAIN STRATEGY =================
def run_strategy():
    symbols = get_symbols()

    ol_list = []
    oh_list = []

    tolerance = 0.05
    buffer = 0.001

    for symbol in symbols[:30]:   # limit for speed
        try:
            # ===== PREVIOUS DAY DATA =====
            daily = yf.download(symbol, period="3d", interval="1d", progress=False)

            if len(daily) < 2:
                continue

            prev_high = daily['High'].iloc[-2]
            prev_low = daily['Low'].iloc[-2]

            # ===== FIRST 5-MIN CANDLE =====
            intraday = yf.download(symbol, period="1d", interval="5m", progress=False)

            if intraday.empty:
                continue

            first = intraday.iloc[0]

            o = first['Open']
            h = first['High']
            l = first['Low']
            c = first['Close']

            # ===== STRATEGY =====

            # 🟢 OPEN ≈ LOW + BREAKOUT
            if abs(o - l) < tolerance and c > prev_high * (1 + buffer):
                ol_list.append({
                    "Symbol": symbol,
                    "Open": round(o, 2),
                    "Low": round(l, 2),
                    "Close": round(c, 2),
                    "PrevHigh": round(prev_high, 2)
                })

            # 🔴 OPEN ≈ HIGH + BREAKDOWN
            if abs(o - h) < tolerance and c < prev_low * (1 - buffer):
                oh_list.append({
                    "Symbol": symbol,
                    "Open": round(o, 2),
                    "High": round(h, 2),
                    "Close": round(c, 2),
                    "PrevLow": round(prev_low, 2)
                })

            time.sleep(0.4)  # avoid rate limits

        except Exception as e:
            print(f"Error {symbol}: {e}")
            continue

    send_email(pd.DataFrame(ol_list), pd.DataFrame(oh_list))


# ================= EMAIL =================
def send_email(df_ol, df_oh):
    sender_email = os.environ["EMAIL"]
    password = os.environ["PASSWORD"]

    recipients = [
        "amitnamo610@gmail.com",
        "vamsidropmail@gmail.com",
        "rmohan1969@gmail.com",
        "navtrade.sol@gmail.com",
        "deepacshekar@gmail.com"
    ]

    html = f"""
    <h2>🟢 Open ≈ Low + Breakout</h2>
    {df_ol.to_html(index=False) if not df_ol.empty else '<p>No stocks found</p>'}

    <br><h2>🔴 Open ≈ High + Breakdown</h2>
    {df_oh.to_html(index=False) if not df_oh.empty else '<p>No stocks found</p>'}
    """

    message = MIMEMultipart()
    message["Subject"] = f"NSE F&O 5-Min Strategy - {datetime.date.today()}"
    message["From"] = f"NSE Alerts <{sender_email}>"
    message["To"] = ", ".join(recipients)

    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipients, message.as_string())


# ================= RUN =================
if __name__ == "__main__":
    run_strategy()
