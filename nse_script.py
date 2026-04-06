import requests
import pandas as pd

def run_nse_task():
    url = "https://www.nseindia.com/api/market-data-pre-open?key=FO"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/"
    }

    session = requests.Session()

    # Step 1: Get cookies
    session.get("https://www.nseindia.com", headers=headers)

    # Step 2: Call API
    response = session.get(url, headers=headers)
    data_json = response.json()

    data = []

    for item in data_json["data"]:
        symbol = item["metadata"]["symbol"]
        final_val = item["detail"]["preOpenMarket"]["finalPrice"]

        if float(final_val).is_integer():
            data.append({
                "symbol": symbol,
                "final": int(final_val)
            })

    if data:
        df = pd.DataFrame(data)
        send_email(df.to_html(index=False))
