def generate_badge(findings):
    SEVERITY_LEVELS = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
    max_severity = -1
    for f in findings:
        sev = SEVERITY_LEVELS.get(f.severity, 0)
        max_severity = max(max_severity, sev)
        
    if len(findings) == 0:
        grade = "A+"
        color = "#4c1"
    elif max_severity == 0:
        grade = "B"
        color = "#97CA00"
    elif max_severity == 1:
        grade = "C"
        color = "#dfb317"
    elif max_severity == 2:
        grade = "D"
        color = "#fe7d37"
    else:
        grade = "F"
        color = "#e05d44"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="100" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="100" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <rect width="65" height="20" fill="#555"/>
    <rect x="65" width="35" height="20" fill="{color}"/>
    <rect width="100" height="20" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="32.5" y="15" fill="#010101" fill-opacity=".3">ciforge</text>
    <text x="32.5" y="14">ciforge</text>
    <text x="81.5" y="15" fill="#010101" fill-opacity=".3">{grade}</text>
    <text x="81.5" y="14">{grade}</text>
  </g>
</svg>"""
    with open("ciforge-badge.svg", "w") as f:
        f.write(svg)
