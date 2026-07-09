import os
import sys

def run():
    print("\n🤖 Welcome to CI Forge! Let's get started.\n")
    print("What would you like to do? (Type a number and press Enter)")
    print("  1) 🛡️  Scan for Vulnerabilities & Code Quality")
    print("  2) 💸 Generate a Cost Report")
    print("  3) 🪄  Fix my code with AI")
    print("  4) 📊 Generate a visual architecture diagram")
    print("  5) 💬 Chat with your codebase")
    print("  6) 🖥️  Launch the Drag-and-Drop Desktop GUI")
    print("  7) ❌ Exit\n")
    
    try:
        choice = input("❯ ")
    except (EOFError, KeyboardInterrupt):
        sys.exit(0)
        
    choice = choice.strip()
    
    cmd = ["ciforge", "--repo", "."]
    if choice == '1':
        print("\nScanning for vulnerabilities...\n")
        cmd.extend(["--vuln-scan", "--format", "html", "--badge"])
    elif choice == '2':
        print("\nGenerating cost report...\n")
        cmd.append("--cost-report")
    elif choice == '3':
        print("\nFiring up Agentic AI Fixer...\n")
        cmd.append("--auto-fix-pr")
    elif choice == '4':
        print("\nGenerating architecture diagram...\n")
        cmd.append("--arch-diagram")
    elif choice == '5':
        print("\nLaunching Codebase Chat...\n")
        cmd.append("--chat")
    elif choice == '6':
        print("\nLaunching Desktop GUI...\n")
        cmd.append("--gui")
    elif choice == '7':
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice.")
        sys.exit(1)
        
    # Re-exec or call main
    os.system(" ".join(cmd))
    sys.exit(0)
