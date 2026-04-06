import pandas as pd
from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import os

def run_nse_task():
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        page = context.new_page()

        page.goto("https://www.nseindia.com", timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        page.goto("https://www.nseindia.com/market-data/pre-open-market-cm-and-emerge-market", timeout=60000)
        page.wait_for_timeout(5000)

        page.select_option('#preOpenMarketSelect', label='Securities in F&O')
        page.wait_for_timeout(5000)

        rows = page.query_selector_all("table tbody tr")

        for row in rows:
            cols = row.query_selector_all("td")
            if len(cols) > 5:
                symbol = cols[0].inner_text().strip()
                final_val = cols[5].inner_text().replace(',', '').strip()

                try:
                    val = float(final_val)
                    if val.is_integer():
                        data.append({
                            "symbol": symbol,
                            "final": int(val)
                        })
                except:
                    pass

        browser.close()

    if data:
        df = pd.DataFrame(data)
        send_email(df.to_html(index=False))


def send_email(table_html):
    sender_email = os.environ["EMAIL"]
    password = os.environ["PASSWORD"]

    recipients = [
        "amitnamo610@gmail.com",
        "vamsidropmail@gmail.com"
    ]

    message = MIMEMultipart()
    message["Subject"] = f"NSE F&O Whole Numbers - {datetime.date.today()}"
    message["From"] = sender_email
    message["To"] = ", ".join(recipients)

    message.attach(MIMEText(table_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipients, message.as_string())


if __name__ == "__main__":
    run_nse_task()
