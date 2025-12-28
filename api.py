from flask import Flask, request
import requests
import json
from datetime import datetime
import pytz
import re

app = Flask(__name__)

# ===== REAL API CONFIG =====
REAL_API = "https://vippanels.x10.mx/numapi.php"
API_KEY = "boss"

# ===== IST TIME =====
def ist_time():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S IST")

# ===== FORMATTER =====
def format_record(item):
    return {
        "mobile": item.get("mobile"),
        "name": item.get("name"),
        "fname": item.get("father_name"),
        "address": item.get("address"),
        "circle": item.get("circle"),
        "id": item.get("id_number"),
        "alt": item.get("alt_mobile"),
        "mail": item.get("email")
    }

# ===== API ENDPOINT =====
@app.route("/api/priyanshu", methods=["GET"])
def priyanshu_api():
    number = request.args.get("number", "")

    # ❌ Invalid number
    if not re.fullmatch(r"\d{10}", number):
        return app.response_class(
            response=json.dumps({
                "success": False,
                "message": "Provide a valid 10-digit mobile number",
                "meta": {
                    "ist": ist_time()
                }
            }, indent=2),
            mimetype="application/json"
        ), 400

    try:
        resp = requests.get(
            REAL_API,
            params={
                "action": "api",
                "key": API_KEY,
                "term": number
            },
            timeout=10
        )

        raw = resp.json()

        if not isinstance(raw, list):
            raise ValueError("Invalid source response")

        data = [format_record(i) for i in raw]

        return app.response_class(
            response=json.dumps({
                "success": True,
                "records": len(data),
                "data": data,
                "meta": {
                    "ist": ist_time()
                }
            }, indent=2),
            mimetype="application/json"
        )

    except Exception:
        return app.response_class(
            response=json.dumps({
                "success": False,
                "message": " prime ids error ",
                "meta": {
                    "ist": ist_time()
                }
            }, indent=2),
            mimetype="application/json"
        ), 500


# --- Run Server ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
