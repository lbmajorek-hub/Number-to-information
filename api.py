from flask import Flask, request, jsonify
import requests, re, time
from datetime import datetime
import pytz
from collections import defaultdict

app = Flask(__name__)

# ================= REAL API =================
REAL_API = "https://api.paanel.shop/numapi.php"
REAL_KEY = "SALAAR"

# ================= API KEYS & LIMITS =================
API_KEYS = {
    "radha": 5,
    "ist": 10,
    "prachi": float("inf")
}

# ================= RULES =================
BLOCKED_NUMBER = "9255939423"
BLOCKED_IPS = set()
NUMBER_HIT_ONCE = set()  # (ip, number)

WINDOW = 86400  # 24 hours

# ================= STORAGE =================
IP_STATS = defaultdict(lambda: {
    "requests_total": 0,
    "lookup_requests": 0,
    "success": 0,
    "error": 0,
    "user_agent": "",
    "method": "",
    "endpoint": "",
    "query": {},
    "limit": 0,
    "first_seen": "",
    "last_seen": "",
    "last_reset": time.time(),
    "blocked": False
})

# ================= TIME =================
def ist_now():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S IST")

def reset_if_needed(ip):
    if time.time() - IP_STATS[ip]["last_reset"] > WINDOW:
        IP_STATS[ip].update({
            "lookup_requests": 0,
            "success": 0,
            "error": 0,
            "last_reset": time.time()
        })

# ================= MAIN API =================
@app.route("/api/priyanshu", methods=["GET"])
def priyanshu_api():

    # 🔥 HIDDEN LOGS (no rate limit)
    if request.args.get("logs") == "ip":
        return jsonify({
            "success": True,
            "ip_logs": IP_STATS
        })

    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "Unknown")
    method = request.method
    endpoint = request.path
    number = request.args.get("number", "")
    key = request.args.get("key", "").lower()

    # INIT LOG
    log = IP_STATS[ip]
    log["requests_total"] += 1
    log["user_agent"] = ua
    log["method"] = method
    log["endpoint"] = endpoint
    log["query"] = {"number": number, "key": key}
    log["last_seen"] = ist_now()
    if not log["first_seen"]:
        log["first_seen"] = log["last_seen"]

    # BLOCKED IP CHECK
    if ip in BLOCKED_IPS:
        log["blocked"] = True
        return jsonify({
            "success": False,
            "message": "Access permanently blocked."
        }), 403

    # NO RATE LIMIT unless LOOKUP
    if not number:
        return jsonify({"success": True, "message": "OK"})

    # LOOKUP STARTS HERE
    reset_if_needed(ip)
    log["lookup_requests"] += 1

    # BLOCKED NUMBER LOGIC
    if number == BLOCKED_NUMBER:
        if (ip, number) in NUMBER_HIT_ONCE:
            BLOCKED_IPS.add(ip)
            log["blocked"] = True
            log["error"] += 1
            return jsonify({
                "success": False,
                "message": "Access permanently blocked."
            }), 403
        else:
            NUMBER_HIT_ONCE.add((ip, number))
            log["error"] += 1
            return jsonify({
                "success": False,
                "message": "This is your father's number. Do not try again."
            }), 403

    # KEY CHECK
    if key not in API_KEYS:
        log["error"] += 1
        return jsonify({
            "success": False,
            "message": "Invalid API key."
        }), 403

    limit = API_KEYS[key]
    log["limit"] = limit

    if log["lookup_requests"] > limit:
        log["error"] += 1
        return jsonify({
            "success": False,
            "message": "Rate limit exceeded. Your access will reset automatically after 24 hours."
        }), 429

    # NUMBER VALIDATION
    if not re.fullmatch(r"\d{10}", number):
        log["error"] += 1
        return jsonify({
            "success": False,
            "message": "Provide a valid 10-digit mobile number."
        }), 400

    # CALL REAL API
    try:
        r = requests.get(
            REAL_API,
            params={"action": "api", "key": REAL_KEY, "number": number},
            timeout=10
        )
        data = r.json()

        if isinstance(data, dict) and (
            data.get("status") == "error"
            or "valid_until" in data
            or "buy api" in str(data).lower()
        ):
            log["error"] += 1
            return jsonify({
                "success": False,
                "message": "Priyanshu ide error"
            }), 500

        log["success"] += 1
        return jsonify({"success": True, "data": data})

    except:
        log["error"] += 1
        return jsonify({
            "success": False,
            "message": "Priyanshu ide error"
        }), 500

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
