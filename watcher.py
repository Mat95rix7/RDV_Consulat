import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import http.client

# Load config
with open("config.json", "r") as f:
    cfg = json.load(f)

WATCH_URL = "https://consulat-creteil-algerie.fr/5589/rendez-vous-passeport-biometrique/"
CURRENT_RDV = datetime.strptime(cfg["current_rdv"], "%Y-%m-%d")

def send_sms(message):
    conn = http.client.HTTPSConnection("api.smsapi.com")
    payload = f"access_token={cfg['sms_token']}&to={cfg['sms_to']}&message={message}"
    headers = {'Content-type': "application/x-www-form-urlencoded"}

    conn.request("POST", "/sms.do", payload, headers)
    conn.getresponse()

def check_rdv():
    html = requests.get(WATCH_URL).text
    soup = BeautifulSoup(html, "html.parser")

    # All days that are clickable
    days = soup.select("a.ui-state-default")

    better_dates = []

    for a in days:
        day = int(a["data-date"])
        month = int(a.parent["data-month"]) + 1    # month is 0-based
        year = int(a.parent["data-year"])
        date = datetime(year, month, day)

        if date < CURRENT_RDV:
            better_dates.append(date)

    if better_dates:
        better_dates.sort()
        best = better_dates[0]
        msg = f"RDV disponible le {best.strftime('%d/%m/%Y')}"
        print(msg)
        send_sms(msg)
    else:
        print("Aucun meilleur RDV trouvé.")

if __name__ == "__main__":
    check_rdv()
