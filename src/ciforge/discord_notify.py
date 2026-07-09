import urllib.request
import json

def send_notification(webhook_url: str, total_findings: int):
    payload = {
        "content": f"CI run completed with {total_findings} findings."
    }
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            pass
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")
