"""Quick local smoke-test against the real ElevenLabs API.

Usage:
    py -3.12 test_api_live.py <your-api-key>
    or set env var ELEVENLABS_API_KEY and run with no args.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

import requests


USER_API_URL = "https://api.elevenlabs.io/v1/user"
ANALYTICS_API_URL = (
    "https://api.elevenlabs.io/v1/workspace/analytics/query/usage-by-product-over-time"
)


def main(api_key: str) -> None:
    headers = {"xi-api-key": api_key}

    # --- /v1/user ---
    print("=== GET /v1/user ===")
    resp = requests.get(USER_API_URL, headers=headers, timeout=15)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 401:
        print("ERROR: 401 Unauthorized — API key is invalid.")
        return
    user_data = resp.json()
    tier = user_data.get("subscription", {}).get("tier")
    print(f"Tier: {tier!r}")
    print(f"Keys in response: {list(user_data.keys())}")

    # --- Analytics windows ---
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    for label, start in [("today", today_start), ("week", week_start), ("month", month_start)]:
        print(f"\n=== Analytics: {label} ({start.date()} -> now) ===")
        payload = {
            "start_time": int(start.timestamp() * 1000),
            "end_time": int(now.timestamp() * 1000),
            "interval_seconds": 86400,
        }
        resp = requests.post(ANALYTICS_API_URL, json=payload, headers=headers, timeout=15)
        print(f"Status: {resp.status_code}")
        if not resp.ok:
            print(f"Error body: {resp.text[:300]}")
            continue
        data = resp.json()
        print(f"columns:      {data.get('columns')}")
        print(f"column_units: {data.get('column_units')}")
        print(f"rows ({len(data.get('rows', []))}): {json.dumps(data.get('rows', [])[:3])}")


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ELEVENLABS_API_KEY", "")
    if not key:
        print("Usage: py -3.12 test_api_live.py <api-key>")
        print("   or: set ELEVENLABS_API_KEY=<key> && py -3.12 test_api_live.py")
        sys.exit(1)
    main(key.strip())
