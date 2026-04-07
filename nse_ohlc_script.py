import requests
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import os


def get_full_data(symbol, session, headers):
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


def run_ohlc_task():
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

    open_high_list = []
    open_low_list = []

    for item in data_json["data"]:
        try:
            symbol = item["metadata"]["symbol"]
            final_val = item["detail"]["preOpenMarket"]["finalPrice"]

            if float(final_val).is_integer():

                d = get_full_data(symbol, session, headers)

                open_p = d["open"]
                high_p = d["high"]
                low_p = d["low"]
                last_p = d["last"]
                prev_close = d["prev_close"]

                # 🔴 OPEN = HIGH
                if open_p == high_p:

                    category = ""

                    if last_p < prev_close:
                        category = "Below Prev Close"

                    open_high_list.append({
                        "symbol": symbol,
                        "open": open_p,
                        "high": high_p,
                        "low": low_p,
                        "category": category
                    })

                # 🟢 OPEN = LOW
                elif open_p == low_p:

                    category = ""

                    if last_p > prev_close:
                        category = "Above Prev Close"

                    open_low_list.append({
                        "symbol": symbol,
                        "open": open_p,
                        "high": high_p,
                        "low": low_p,
                        "category": category
                    })

        except:
            continue

    # Email formatting
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
        "vamsidropmail@gmail.com"
    ]

    message = MIMEMultipart()
    message["Subject"] = f"NSE Open=High / Open=Low (9:21) - {datetime.date.today()}"
    message["From"] = f"NSE Alerts (Do Not Reply) <{sender_email}>"
    message["To"] = ", ".join(recipients)

    message.attach(MIMEText(table_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipients, message.as_string())


if __name__ == "__main__":
    run_ohlc_task()
