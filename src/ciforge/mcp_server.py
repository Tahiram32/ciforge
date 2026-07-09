import sys
import json
import os
from dataclasses import asdict
from . import vuln_scan, dead_code, iac_scan, duplication

def handle_request(req):
    method = req.get("method")
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "ciforge",
                "version": "5.0.0"
            }
        }
    elif method == "tools/list":
        return {
            "tools": [
                {
                    "name": "ciforge_scan",
                    "description": "Run core CIForge scanners (vuln, dead_code, iac, dupe)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Path to the directory to scan"
                            }
                        },
                        "required": ["directory"]
                    }
                }
            ]
        }
    elif method == "tools/call":
        params = req.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})
        
        if name == "ciforge_scan":
            directory = args.get("directory", ".")
            orig_dir = os.getcwd()
            findings = []
            try:
                if os.path.exists(directory):
                    os.chdir(directory)
                findings.extend(vuln_scan.analyze())
                findings.extend(dead_code.analyze())
                findings.extend(iac_scan.analyze())
                findings.extend(duplication.analyze())
            except Exception as e:
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": str(e)}]
                }
            finally:
                os.chdir(orig_dir)
                
            return {
                "content": [{"type": "text", "text": json.dumps([asdict(f) for f in findings])}]
            }
    
    return {}

def serve():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
            
        if "id" in req:
            result = handle_request(req)
            resp = {
                "jsonrpc": "2.0",
                "id": req["id"],
                "result": result
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
