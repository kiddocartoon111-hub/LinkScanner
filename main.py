import requests
import os
import csv
from datetime import datetime, timedelta

# --- SETTINGS ---
SHEET_URL = "APNI_GOOGLE_SHEET_CSV_URL_YAHAN_DALO" # Niche batata hoon ye kahan se milega
SCRAPER_API_KEY = os.environ.get('SCRAPER_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_sheet_data():
    response = requests.get(SHEET_URL)
    decoded_content = response.content.decode('utf-8')
    cr = csv.DictReader(decoded_content.splitlines(), delimiter=',')
    return list(cr)

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def check_link(url):
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    try:
        res = requests.get(proxy_url, timeout=30)
        if res.status_code == 200:
            if "Currently unavailable" in res.text: return "⚠️ OUT OF STOCK"
            return "✅ ACTIVE"
        return "❌ BROKEN"
    except: return "🚨 DOWN"

# --- MAIN ENGINE ---
today = datetime.now()
data = get_sheet_data()

for row in data:
    name = row['Name']
    link = row['Link']
    plan = row['Plan']
    join_dt = datetime.strptime(row['Join_Date'], "%Y-%m-%d")
    
    # Plan Limit
    limit = 7 if plan == "Free" else 30
    expiry_dt = join_dt + timedelta(days=limit)
    
    if today > expiry_dt:
        # Plan Expired: Data sheet mein rahega, par scan nahi hoga
        print(f"Skipping {name}: Plan Expired")
        send_telegram(f"🚫 *SCAN STOPPED*\nUser: {name}\nReason: Plan Expired. Bhai payment mang lo!")
        continue

    # Agar Plan Active hai, tabhi scan karo
    status = check_link(link)
    if "✅" not in status:
        send_telegram(f"❗ *ISSUE*: {name}\nStatus: {status}\nLink: {link}")
