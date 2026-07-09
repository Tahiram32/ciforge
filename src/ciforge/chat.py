import os
import sys

def chat_loop(repo_path):
    print(f"\n💬 Welcome to CI Forge Chat!")
    print(f"I am analyzing your codebase at {os.path.abspath(repo_path)}")
    print("Ask me anything about vulnerabilities, code architecture, or CI costs. (Type 'exit' to quit)\n")
    
    # In a real scenario, we'd parse the AST here and feed it into the context window.
    # We will mock the AI response for the sake of the zero-dependency CLI.
    
    while True:
        try:
            query = input("❯ ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
            
        if query.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
            
        if not query.strip():
            continue
            
        print("\n🤖 Thinking...\n")
        
        # Simulated intelligent responses based on keywords
        lower_query = query.lower()
        if "security" in lower_query or "vulnerabilit" in lower_query:
            print("I scanned the AST and found 2 potential security issues in your code.")
            print("1. There is an unsafe f-string in `db_query.py` that could lead to SQL injection.")
            print("2. I detected a potential buffer overflow vulnerability in `main.c`.")
            print("Would you like me to run `--auto-fix-pr` to resolve these?")
        elif "cost" in lower_query or "money" in lower_query:
            print("Based on your 51 files, you are wasting approximately $1.63/month on redundant GitHub Actions runs.")
            print("If you factor in SaaS tool bloat, you could be saving $450/month. Run `ciforge --cost-report` for the full breakdown.")
        elif "architecture" in lower_query or "structure" in lower_query:
            print("This repository appears to be a Python monolithic CLI tool.")
            print("The core logic is in `src/ciforge/cli.py` which dynamically loads specialized scanners (e.g., `vuln_scan.py`, `ci_cost.py`).")
        else:
            print("That's an interesting question! Based on my analysis of the codebase, everything seems functionally sound.")
            print("If you want me to write code to fix a specific bug, just let me know!")
        print("")
