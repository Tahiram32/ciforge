import os
import urllib.request
import json
import traceback

def report_crash(exception: Exception, module_name: str):
    webhook_url = os.environ.get("CIFORGE_CRASH_WEBHOOK")
    if not webhook_url:
        return

    try:
        # Extract the traceback safely
        tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        # To avoid private code context, we could just include the module name, exception type and message
        # or limit the traceback. For now, let's include the traceback lines but the user instruction says:
        # "(without private code context if possible)".
        # It's safer to just send the exception type, string representation, and the module name,
        # but traceback usually includes file paths and lines. Let's send a simplified traceback if needed,
        # or just the standard one if we assume it doesn't contain source code content, or we can use traceback.extract_tb
        
        # Let's extract traceback without source lines if possible, or just the error message and standard tb
        # For simplicity and compliance:
        tb_summary = traceback.extract_tb(exception.__traceback__)
        clean_tb = []
        for frame in tb_summary:
            clean_tb.append(f"File {os.path.basename(frame.filename)}, line {frame.lineno}, in {frame.name}")
            
        data = {
            "module_name": module_name,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": clean_tb
        }
        
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(webhook_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            pass
    except Exception:
        # Silently ignore telemetry errors
        pass

def report_ai_finding(message: str):
    webhook_url = os.environ.get("CIFORGE_AI_WEBHOOK")
    if not webhook_url:
        return

    try:
        data = {
            "finding_message": message
        }
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(webhook_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            pass
    except Exception:
        # Silently ignore telemetry errors
        pass
