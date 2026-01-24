import requests
import os
import csv
from datetime import datetime, timedelta

# --- SETTINGS FROM GITHUB SECRETS ---
SHEET_URL = os.environ.get('SHEET_URL')
SCRAPER_API_KEY = os.environ.get('SCRAPER_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_sheet_data():
    try:
        response = requests.get(SHEET_URL)
        response.raise_for_status()
        decoded_content = response.content.decode('utf-8')
        cr = csv.DictReader(decoded_content.splitlines(), delimiter=',')
        return list(cr)
    except Exception as e:
        print(f"Sheet Download Error: {e}")
        return []

def check_link(url):
    # Amazon bypass using ScraperAPI
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    try:
        res = requests.get(proxy_url, timeout=30)
        if res.status_code == 200:
            if "Currently unavailable" in res.text:
                return "🚨 OUT OF STOCK"
            return "✅ ACTIVE"
        return f"❌ BROKEN ({res.status_code})"
    except:
        return "🚨 SERVER DOWN"

# --- MAIN ENGINE ---
print("🚀 Launching Link Scanner Pro...")
data = get_sheet_data()
today = datetime.now()

for row in data:
    name = row.get('Name', 'Unknown')
    link = row.get('Link', '')
    plan = row.get('Plan', 'Free').strip()
    join_date_str = row.get('Join_Date', '')

    if not link or not join_date_str:
        continue

    # --- SUBSCRIPTION LOGIC ---
    try:
        join_dt = datetime.strptime(join_date_str, "%Y-%m-%d")
    except:
        print(f"Invalid Date Format for {name}. Use YYYY-MM-DD")
        continue

    # Plan ke hisaab se expiry set karein
    plan_lower = plan.lower()
    if "early" in plan_lower:
        limit_days = 365
    elif "paid" in plan_lower:
        limit_days = 30
    else: # Default: Free
        limit_days = 7
        
    expiry_dt = join_dt + timedelta(days=limit_days)

    # Check if Plan is Expired
    if today > expiry_dt:
        print(f"🚫 Plan Expired for {name} ({plan})")
        # Har 1-2 din mein alert bhejega jab tak date change na ho
        send_telegram(f"⚠️ *PLAN EXPIRED ALERT*\n\n*User:* {name}\n*Plan:* {plan}\n*Status:* Scanning Stopped\n\nBhai, iska subscription khatam ho gaya hai. Payment renew karne ko bolo!")
        continue

    # --- SCANNING (Sirf Active Plans ke liye) ---
    print(f"🔍 Checking: {name}...")
    status = check_link(link)
    
    if "✅" not in status:
        send_telegram(f"❗ *LINK ISSUE*: {name}\n*Status*: {status}\n*Link*: {link}")

print("✅ All tasks finished!")
