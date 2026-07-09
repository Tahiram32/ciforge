import concurrent.futures
import urllib.request
import time
from .scanner import Finding

def fetch(url):
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'ciforge-load-test'})
        with urllib.request.urlopen(req, timeout=5) as response:
            response.read()
            return time.time() - start, None
    except Exception as e:
        return time.time() - start, e

def analyze(url: str) -> list[Finding]:
    findings = []
    times = []
    errors = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(fetch, url) for _ in range(50)]
        for future in concurrent.futures.as_completed(futures):
            t, err = future.result()
            times.append(t)
            if err:
                errors += 1
                
    avg_time = sum(times) / len(times) if times else 0
    
    if avg_time > 1.5 or errors > 0:
        msg = f"Load Test Failed: Average latency {avg_time:.2f}s exceeds threshold"
        if errors > 0:
            msg += f" (Errors: {errors})"
        findings.append(Finding(
            file=url,
            line=0,
            message=msg,
            severity="high"
        ))
        
    return findings
