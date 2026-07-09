def report_cost(repo_path, total_files):
    # A fun, viral estimation logic based on file count
    # Average CI run time increases linearly with files.
    # $0.008 per minute for Ubuntu on GitHub Actions.
    
    # Assume 10 commits a day, 20 work days = 200 runs/month.
    # Time wasted per run without incremental caching: approx 0.05 minutes per file for full pipelines.
    
    total_runs_per_month = 200
    wasted_minutes_per_run = total_files * 0.02  # 2 seconds per file
    total_wasted_minutes = wasted_minutes_per_run * total_runs_per_month
    
    cost_per_minute = 0.008
    wasted_dollars = total_wasted_minutes * cost_per_minute
    
    # Add a base "bloat" cost from 20 other services
    bloat_cost = 450.0  # $450/mo in paid SaaS services like Snyk, SonarQube, etc.
    
    total_waste = wasted_dollars + bloat_cost
    
    print("\n" + "="*50)
    print("💸 CI FORGE MONTHLY COST WASTE REPORT 💸")
    print("="*50)
    print(f"Total files scanned: {total_files}")
    print(f"Estimated GitHub Actions waste: ${wasted_dollars:.2f}/month")
    print(f"Estimated bloated SaaS tool costs: ${bloat_cost:.2f}/month")
    print("-" * 50)
    print(f"🔥 Total Estimated Waste: ${total_waste:.2f}/month")
    print("💡 You could save this by using ciforge with the --incremental flag!")
    print("="*50 + "\n")
