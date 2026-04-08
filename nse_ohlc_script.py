import requests
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import os
import pytz

# ================= TIME CONTROL =================
ist = pytz.timezone('Asia/Kolkata')
now = datetime.datetime.now(ist)

# Allow only between 9:15–9:25 AM IST
if not (now.hour == 9 and 15 <= now.minute <= 25):
    print(f"Skipped execution at {now}")
    exit()

# ================= DUPLICATE CONTROL =================
today_str = now.strftime("%Y-%m-%d")
FLAG_FILE = f"ohlc_sent_{today_str}.flag"

if os.path.exists(FLAG_FILE):
    print("Mail already sent today")
    exit()

# ================= NSE SESSION =================
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com/"
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers)

# ================= FUNCTIONS =================

def get_full_data(symbol):
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
    response = session.get(url, headers=headers, timeout=10)
    data = response.json()

    price = data["priceInfo"]

    return {
        "open": price["open"],
        "high": price["intraDayHighLow"]["max"],
        "low": price["intraDayHighLow"]["min"],
        "last": price["lastPrice"],
        "prev_close": price["previousClose"]
    }


def get_prev_day_levels(symbol):
    today = datetime.date.today()
    prev_day = today - datetime.timedelta(days=1)
    date_str = prev_day.strftime("%d-%m-%Y")

    url = f"https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}&series=[%22EQ%22]&from={date_str}&to={date_str}"
    response = session.get(url, headers=headers, timeout=10)
    data = response.json()

    if "data" in data and len(data["data"]) > 0:
        d = data["data"][0]
        return {
            "prev_high": d["CH_TRADE_HIGH_PRICE"],
            "prev_low": d["CH_TRADE_LOW_PRICE"]
        }

    return {"prev_high": None, "prev_low": None}


# ================= MAIN LOGIC =================

def run_ohlc_task():
    url = "https://www.nseindia.com/api/market-data-pre-open?key=FO"
    response = session.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        print("API failed:", response.status_code)
        return

    data_json = response.json()

    open_high_list = []
    open_low_list = []

    tolerance = 0.1  # IMPORTANT FIX

    for item in data_json["data"]:
        try:
            symbol = item["metadata"]["symbol"]
            final_val = item["detail"]["preOpenMarket"]["finalPrice"]

            if float(final_val).is_integer():

                d = get_full_data(symbol)
                prev = get_prev_day_levels(symbol)

                open_p = d["open"]
                high_p = d["high"]
                low_p = d["low"]
                last_p = d["last"]
                prev_close = d["prev_close"]

                prev_high = prev["prev_high"]
                prev_low = prev["prev_low"]

                # 🔴 OPEN ≈ HIGH
                if abs(open_p - high_p) < tolerance:

                    category = []

                    if prev_low and low_p < prev_low:
                        category.append("PDL Broken")

                    if last_p < prev_close:
                        category.append("Below Prev Close")

                    open_high_list.append({
                        "symbol": symbol,
                        "open": open_p,
                        "high": high_p,
                        "low": low_p,
                        "category": ", ".join(category)
                    })

                # 🟢 OPEN ≈ LOW
                elif abs(open_p - low_p) < tolerance:

                    category = []

                    if prev_high and high_p > prev_high:
                        category.append("PDH Broken")

                    if last_p > prev_close:
                        category.append("Above Prev Close")

                    open_low_list.append({
                        "symbol": symbol,
                        "open": open_p,
                        "high": high_p,
                        "low": low_p,
                        "category": ", ".join(category)
                    })

        except Exception as e:
            print(f"Error {symbol}: {e}")
            continue

    # ================= EMAIL =================

    html = "<h2>🔴 Open ≈ High Stocks</h2>"

    if open_high_list:
        df_high = pd.DataFrame(open_high_list).sort_values(by="symbol")
        html += df_high.to_html(index=False)
    else:
        html += "<p>No stocks found</p>"

    html += "<br><h2>🟢 Open ≈ Low Stocks</h2>"

    if open_low_list:
        df_low = pd.DataFrame(open_low_list).sort_values(by="symbol")
        html += df_low.to_html(index=False)
    else:
        html += "<p>No stocks found</p>"

    send_email(html)

    # Mark as sent
    with open(FLAG_FILE, "w") as f:
        f.write("sent")


def send_email(table_html):
    sender_email = os.environ["EMAIL"]
    password = os.environ["PASSWORD"]

    recipients = [
        "amitnamo610@gmail.com",
        "vamsidropmail@gmail.com",
        "rmohan1969@gmail.com",
        "navtrade.sol@gmail.com",
        "deepacshekar@gmail.com"
    ]

    message = MIMEMultipart()
    message["Subject"] = f"NSE OHOL Strategy - {datetime.date.today()}"
    message["From"] = f"NSE Alerts <{sender_email}>"
    message["To"] = ", ".join(recipients)

    message.attach(MIMEText(table_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipients, message.as_string())


if __name__ == "__main__":
    run_ohlc_task()
