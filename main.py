import requests, os, csv, time
from datetime import datetime, timedelta

# ================= CONFIG =================
SHEET_URL = os.getenv("SHEET_URL")
SCRAPER_API_KEY = os.getenv("SCRAPER_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (LinkGuardBot/1.0)"
}

BROKEN_WORDS = [
    "page not found",
    "404",
    "currently unavailable",
    "out of stock",
    "link expired",
    "sorry, this page isn't available"
]

PLAN_DAYS = {
    "7-day trial": 7,
    "monthly": 30,
    "early access": 365
}

# ================= HELPERS =================
def tg(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg})

def normal_check(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        return r.status_code == 200, r.text.lower()
    except:
        return False, ""

def deep_check(url):
    api = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true"
    try:
        r = requests.get(api, timeout=60)
        return r.status_code == 200, r.text.lower()
    except:
        return False, ""

def expired(plan, join_date):
    days = PLAN_DAYS.get(plan.lower(), 7)
    return datetime.now() > (join_date + timedelta(days=days))

# ================= ENGINE =================
print("🚀 LinkGuard Scanner Started")

rows = []
csv_data = requests.get(SHEET_URL).content.decode("utf-8")
rows = list(csv.DictReader(csv_data.splitlines()))

for row in rows:
    try:
        name = row["User_Name"]
        insta = row["Instagram"]
        phone = row["WhatsApp"]
        plan = row["Plan"]
        link_name = row["Link_Name"]
        link = row["Link_URL"]
        join_date = datetime.strptime(row["Join_Date"], "%Y-%m-%d")
    except:
        continue

    if expired(plan, join_date):
        continue

    ok, text = normal_check(link)

    if not ok:
        time.sleep(5)
        ok, text = deep_check(link)

    issue = None
    if not ok:
        issue = "Link Down"
    else:
        for w in BROKEN_WORDS:
            if w in text:
                issue = f"Issue detected: {w}"
                break

    if issue:
        tg(
            f"🚨 LINK ALERT\n\n"
            f"👤 {name}\n"
            f"📸 @{insta}\n"
            f"🔗 {link_name}\n"
            f"🌐 {link}\n"
            f"📞 {phone}\n"
            f"⚠️ {issue}"
        )

    time.sleep(2)

print("✅ Scan Complete")
