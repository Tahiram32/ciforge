import os
import json

def get_welcome_message():
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not os.path.exists(event_path):
        return None
        
    try:
        with open(event_path, "r") as f:
            data = json.load(f)
            if "pull_request" in data:
                author_assoc = data["pull_request"].get("author_association")
                if author_assoc in ("FIRST_TIMER", "FIRST_TIME_CONTRIBUTOR"):
                    return "🎉 Welcome! Thank you for your first contribution!"
    except Exception:
        pass
    
    return None
