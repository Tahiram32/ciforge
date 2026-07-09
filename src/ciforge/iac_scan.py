import os
import re
import glob
from .scanner import Finding

def scan_dockerfile(path):
    findings = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if re.match(r'^\s*USER\s+root\s*$', line, re.IGNORECASE):
                    findings.append(Finding(file=path, line=i, message="USER root is an anti-pattern in Dockerfile.", severity="high"))
                if '0.0.0.0' in line:
                    findings.append(Finding(file=path, line=i, message="0.0.0.0 exposure in Dockerfile.", severity="high"))
    return findings

def scan_docker_compose(path):
    findings = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if '0.0.0.0' in line:
                    findings.append(Finding(file=path, line=i, message="0.0.0.0 exposure in docker-compose.yml.", severity="high"))
    return findings

def scan_tf(path):
    findings = []
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            if '0.0.0.0' in line:
                findings.append(Finding(file=path, line=i, message="0.0.0.0 exposure in Terraform file.", severity="high"))
            if re.search(r'(access_key|secret_key)\s*=\s*["\'][A-Za-z0-9/+=]+["\']', line):
                findings.append(Finding(file=path, line=i, message="Plaintext AWS keys found in Terraform file.", severity="high"))
    return findings

def analyze() -> list[Finding]:
    findings = []
    findings.extend(scan_dockerfile('Dockerfile'))
    findings.extend(scan_docker_compose('docker-compose.yml'))
    for tf_file in glob.glob('**/*.tf', recursive=True):
        findings.extend(scan_tf(tf_file))
    return findings
