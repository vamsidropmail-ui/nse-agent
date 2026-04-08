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

# Allow only between 9:08–9:12 AM IST
if not (now.hour == 9 and 8 <= now.minute <= 12):
    print(f"Skipped execution at {now}")
    exit()

# ================= DUPLICATE CONTROL =================
today_str = now.strftime("%Y-%m-%d")
FLAG_FILE = f"sent_{today_str}.flag"

if os.path.exists(FLAG_FILE):
    print("Mail already sent today")
    exit()


def run_nse_task():
    url = "https://www.nseindia.com/api/market-data-pre-open?key=FO"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/"
    }

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)

    response = session.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        print("API failed:", response.status_code)
        return

    data_json = response.json()

    data = []

    for item in data_json["data"]:
        try:
            symbol = item["metadata"]["symbol"]
            final_val = item["detail"]["preOpenMarket"]["finalPrice"]

            if float(final_val).is_integer():
                data.append({
                    "symbol": symbol,
                    "final": int(float(final_val))
                })
        except:
            continue

    if data:
        df = pd.DataFrame(data)
        df = df.sort_values(by="symbol").reset_index(drop=True)
        html = df.to_html(index=False)
    else:
        html = "<h3>No stocks found with whole number prices today</h3>"

    send_email(html)

    # Create flag AFTER successful email
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
    message["Subject"] = f"NSE F&O Whole Price Stocks - {datetime.date.today()}"
    message["From"] = f"NSE Alerts (Do Not Reply) <{sender_email}>"
    message["To"] = ", ".join(recipients)

    message.attach(MIMEText(table_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipients, message.as_string())


if __name__ == "__main__":
    run_nse_task()
