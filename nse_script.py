import requests
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import os


def run_nse_task():
    url = "https://www.nseindia.com/api/market-data-pre-open?key=FO"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/"
    }

    # Create session and get cookies
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)

    # Fetch API data
    response = session.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        print("API failed:", response.status_code)
        return

    data_json = response.json()

    data = []

    # Extract required data
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

    # Process and send email
    if data:
    df = pd.DataFrame(data)
    df = df.sort_values(by="symbol").reset_index(drop=True)
    html = df.to_html(index=False)
else:
    html = "<h3>No stocks found with whole number prices today</h3>"

send_email(html)


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
