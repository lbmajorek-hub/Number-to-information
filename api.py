from flask import Flask, request, jsonify
import requests, re, time
from datetime import datetime
import pytz
from collections import defaultdict

app = Flask(__name__)

# ================= REAL APIs =================
PRIMARY_API = "https://api.x10.network/numapi.php"
PRIMARY_KEY = "kasa"

BACKUP_API = "https://api.x10.network/numapi.php"
BACKUP_KEY = "SALAAR"

# ================= API KEYS & LIMITS =================
API_KEYS = {
    "Purvi": 5,
    "Ist": 10,
    "Priyanshu": float("inf")
}

# ================= STORAGE =================
IP_STATS = defaultdict(lambda: {
    "requests": 0,
    "user_agent": "",
    "last_reset": time.time(),
    "limit": 0
})

WINDOW = 86400  # 24 hours

# ================= IST TIME =================
def ist_time():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S IST")

# ================= RESET CHECK =================
def reset_if_needed(ip):
    if time.time() - IP_STATS[ip]["last_reset"] > WINDOW:
        IP_STATS[ip]["requests"] = 0
        IP_STATS[ip]["last_reset"] = time.time()

# ================= MAIN API =================
@app.route("/api/priyanshu", methods=["GET"])
def priyanshu_api():

    # 🔥 HIDDEN IP LOGS (same endpoint)
    if request.args.get("logs") == "ip":
        return jsonify({
            "success": True,
            "ip_logs": {
                ip: {
                    "requests": data["requests"],
                    "limit": ("unlimited" if data["limit"] == float("inf") else data["limit"]),
                    "remaining": (
                        "unlimited" if data["limit"] == float("inf")
                        else max(data["limit"] - data["requests"], 0)
                    ),
                    "user_agent": data["user_agent"],
                    "reset_after": int(max(WINDOW - (time.time() - data["last_reset"]), 0))
                }
                for ip, data in IP_STATS.items()
            }
        })

    # ---------- NORMAL FLOW ----------
    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent", "Unknown")
    number = request.args.get("number", "")
    key = request.args.get("key", "")

    # API KEY CHECK
    if key not in API_KEYS:
        return jsonify({
            "success": False,
            "message": "Invalid API key."
        }), 403

    # NUMBER CHECK
    if not re.fullmatch(r"\d{10}", number):
        return jsonify({
            "success": False,
            "message": "Provide a valid 10-digit mobile number."
        }), 400

    reset_if_needed(ip)

    limit = API_KEYS[key]
    IP_STATS[ip]["limit"] = limit

    if IP_STATS[ip]["requests"] >= limit:
        return jsonify({
            "success": False,
            "message": "Rate limit exceeded. Your access will reset automatically after 24 hours."
        }), 429

    # COUNT + UA
    IP_STATS[ip]["requests"] += 1
    IP_STATS[ip]["user_agent"] = user_agent

    # TRY PRIMARY API
    try:
        r = requests.get(PRIMARY_API, params={
            "action": "api",
            "key": PRIMARY_KEY,
            "number": number
        }, timeout=10)

        if r.status_code == 200:
            return jsonify({
                "success": True,
                "data": r.json()
            })
    except:
        pass

    # TRY BACKUP API
    try:
        r = requests.get(BACKUP_API, params={
            "action": "api",
            "key": BACKUP_KEY,
            "number": number
        }, timeout=10)

        if r.status_code == 200:
            return jsonify({
                "success": True,
                "data": r.json()
            })
    except:
        pass

    return jsonify({
        "success": False,
        "message": "Priyanshu ide error"
    }), 500

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
