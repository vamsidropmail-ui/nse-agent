import requests
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import os


def get_ohlc(symbol, session, headers):
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"

    response = session.get(url, headers=headers, timeout=10)
    data = response.json()

    price = data["priceInfo"]

    return {
        "open": price["open"],
        "high": price["intraDayHighLow"]["max"],
        "low": price["intraDayHighLow"]["min"]
    }


def run_ohlc_task():
    url = "https://www.nseindia.com/api/market-data-pre-open?key=FO"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/"
    }

    # Create session
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)

    # Get F&O list
    response = session.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        print("API failed:", response.status_code)
        return

    data_json = response.json()

    open_high_list = []
    open_low_list = []

    # Loop through stocks
    for item in data_json["data"]:
        try:
            symbol = item["metadata"]["symbol"]
            final_val = item["detail"]["preOpenMarket"]["finalPrice"]

            # Keep your original filter (whole number)
            if float(final_val).is_integer():

                ohlc = get_ohlc(symbol, session, headers)

                if ohlc["open"] == ohlc["high"]:
                    open_high_list.append({
                        "symbol": symbol,
                        "open": ohlc["open"],
                        "high": ohlc["high"]
                    })

                elif ohlc["open"] == ohlc["low"]:
                    open_low_list.append({
                        "symbol": symbol,
                        "open": ohlc["open"],
                        "low": ohlc["low"]
                    })

        except:
            continue

    # Prepare email HTML
    html = "<h2>Open = High Stocks</h2>"

    if open_high_list:
        df_high = pd.DataFrame(open_high_list).sort_values(by="symbol")
        html += df_high.to_html(index=False)
    else:
        html += "<p>No stocks found</p>"

    html += "<br><h2>Open = Low Stocks</h2>"

    if open_low_list:
        df_low = pd.DataFrame(open_low_list).sort_values(by="symbol")
        html += df_low.to_html(index=False)
    else:
        html += "<p>No stocks found</p>"

    send_email(html)


def send_email(table_html):
    sender_email = os.environ["EMAIL"]
    password = os.environ["PASSWORD"]

    recipients = [
        "vamsidropmail@gmail.com",
        "vamsidropmail@gmail.com"
    ]

    message = MIMEMultipart()
    message["Subject"] = f"NSE Open=High / Open=Low - {datetime.date.today()}"
    message["From"] = f"NSE Alerts (Do Not Reply) <{sender_email}>"
    message["To"] = ", ".join(recipients)

    message.attach(MIMEText(table_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipients, message.as_string())


if __name__ == "__main__":
    run_ohlc_task()
