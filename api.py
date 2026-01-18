from flask import Flask, request, jsonify
import requests, re, time
from datetime import datetime
import pytz
from collections import defaultdict

app = Flask(__name__)

# ================= REAL API (ONLY ONE) =================
REAL_API = "https://api.x10.network/numapi.php"
REAL_KEY = "SALAAR"

# ================= API KEYS & LIMITS =================
API_KEYS = {
    "purvi": 5,
    "ist": 10,
    "priyanshu": float("inf")
}

# ================= STORAGE =================
IP_STATS = defaultdict(lambda: {
    "requests": 0,
    "success": 0,
    "error": 0,
    "user_agent": "",
    "last_reset": time.time(),
    "limit": 0
})

WINDOW = 86400  # 24 hours

# ================= TIME =================
def ist_time():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S IST")

# ================= RESET =================
def reset_if_needed(ip):
    if time.time() - IP_STATS[ip]["last_reset"] > WINDOW:
        IP_STATS[ip].update({
            "requests": 0,
            "success": 0,
            "error": 0,
            "last_reset": time.time()
        })

# ================= MAIN API =================
@app.route("/api/priyanshu", methods=["GET"])
def priyanshu_api():

    # 🔥 HIDDEN IP LOGS
    if request.args.get("logs") == "ip":
        return jsonify({
            "success": True,
            "ip_logs": {
                ip: {
                    "requests": d["requests"],
                    "success": d["success"],
                    "error": d["error"],
                    "limit": ("unlimited" if d["limit"] == float("inf") else d["limit"]),
                    "remaining": (
                        "unlimited" if d["limit"] == float("inf")
                        else max(d["limit"] - d["requests"], 0)
                    ),
                    "user_agent": d["user_agent"],
                    "reset_after_seconds": int(
                        max(WINDOW - (time.time() - d["last_reset"]), 0)
                    )
                }
                for ip, d in IP_STATS.items()
            }
        })

    # ---------- NORMAL FLOW ----------
    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent", "Unknown")
    number = request.args.get("number", "")
    key = request.args.get("key", "").lower()

    reset_if_needed(ip)

    # API KEY CHECK (COUNT EVEN IF INVALID)
    IP_STATS[ip]["requests"] += 1
    IP_STATS[ip]["user_agent"] = user_agent

    if key not in API_KEYS:
        IP_STATS[ip]["error"] += 1
        return jsonify({
            "success": False,
            "message": "Invalid API key."
        }), 403

    limit = API_KEYS[key]
    IP_STATS[ip]["limit"] = limit

    if IP_STATS[ip]["requests"] > limit:
        IP_STATS[ip]["error"] += 1
        return jsonify({
            "success": False,
            "message": "Rate limit exceeded. Your access will reset automatically after 24 hours."
        }), 429

    # NUMBER CHECK (ALSO COUNTS)
    if not re.fullmatch(r"\d{10}", number):
        IP_STATS[ip]["error"] += 1
        return jsonify({
            "success": False,
            "message": "Provide a valid 10-digit mobile number."
        }), 400

    # CALL REAL API
    try:
        r = requests.get(
            REAL_API,
            params={
                "action": "api",
                "key": REAL_KEY,
                "number": number
            },
            timeout=10
        )

        data = r.json()

        # ❌ ANY ERROR / valid_until / buy api msg → hide it
        if isinstance(data, dict) and (
            data.get("status") == "error"
            or "valid_until" in data
            or "buy api" in str(data).lower()
        ):
            IP_STATS[ip]["error"] += 1
            return jsonify({
                "success": False,
                "message": "Priyanshu ide error"
            }), 500

        # ✅ SUCCESS
        IP_STATS[ip]["success"] += 1
        return jsonify({
            "success": True,
            "data": data
        })

    except:
        IP_STATS[ip]["error"] += 1
        return jsonify({
            "success": False,
            "message": "Priyanshu ide error"
        }), 500

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
