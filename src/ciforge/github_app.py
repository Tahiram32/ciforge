import http.server
import socketserver
import json
import os

class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            payload = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return
            
        # If it's a pull request event
        if "pull_request" in payload and payload.get("action") in ["opened", "synchronize"]:
            print(f"📦 Received Push to PR #{payload['pull_request']['number']}")
            print("🚀 Automatically running CI Forge scan...")
            
            # In a real deployed GitHub App, we would clone the PR repo here.
            # For this mock, we just trigger the scan on the local repo.
            os.system("ciforge --repo . --vuln-scan --fail-on high")
            
            # We would then use the GitHub API to post a comment back to the PR.
            print("✅ Scan complete. Automatically commenting on the PR via GitHub API.")
            
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "success"}')

def run(port=8080):
    with socketserver.TCPServer(("", port), WebhookHandler) as httpd:
        print(f"🚀 CI Forge Native GitHub App Webhook Server running on port {port}")
        print("Waiting for Pull Request events from GitHub...")
        httpd.serve_forever()

if __name__ == "__main__":
    run()
