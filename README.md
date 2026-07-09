# ciforge

[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-ea4aaa?logo=github-sponsors)](https://github.com/sponsors/Tahiram32)
[![PyPI](https://img.shields.io/pypi/v/ciforge-cli)](https://pypi.org/project/ciforge-cli/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPLv3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**ciforge** is a zero-dependency CLI and GitHub Action that replaces 20 CI services with one robust tool. Run your complete CI pipeline 100% locally or natively within your actions, faster and with zero external dependencies.

## Features

- **Code Quality**: Intelligent linting and AST-based complexity analysis (cyclomatic complexity, long functions).
- **Test Coverage Analysis**: Deep inspection of test coverage gaps.
- **Secret Detection**: Catch hardcoded credentials before they reach your repository.
- **Config Validation**: Native parsing and validation for JSON, YAML, ENV, TOML, and XML files.
- **PR Metrics & Velocity Tracking**: Analyze pull request size, churn, and time span metrics.
- **Multi-Model AI Review**: Integrates with OpenAI, Anthropic, or Ollama to find logic flaws and missing edge cases.
- **Localization Sync**: Finds missing translation keys by comparing localization files against a base en.json.
- **Git Hooks Installer**: Easily install pre-commit hooks to run ciforge before committing.
- **Auto-Generated Badges**: Generate dynamic SVG badges reflecting repository health.
- **HTML Reports**: Export beautiful standalone HTML reports.
- **Contributor Welcome Module**: Automatically greet first-time contributors.
- **Auto-Fixer (`--fix`)**: Automatically resolves low-hanging issues like debug statements and bad formatting.
- **Custom Ignore Rules**: Whitelist files and dummy secrets via `.ciforge-ignore`.
- **Auto-Changelog Generator**: Generate `CHANGELOG.md` from git log using conventional commits.
- **Dead Code Detector**: Find unreferenced functions and classes.
- **Deployment Health Check**: Verify production deployments after CI runs.
- **Config Drift Detection**: Detect out-of-sync environment files (e.g. `.env.production` vs `.env.staging`).
- **Architecture Diagram Generator**: Auto-generate Mermaid dependency diagrams.
- **Auto PR Descriptions**: Generate rich markdown PR descriptions from git diffs.
- **Mobile Config Linter**: Catch errors in `pubspec.yaml`, `build.gradle`, and `Podfile`.
- **Blast Radius Radar**: AST-based analysis of Python imports to identify highly-coupled "God files".
- **MCP Hygiene Scanner**: Validates `mcp.config.jsonc` files for secure Model Context Protocol server configuration.
- **Schema Guardian**: Automatically detects breaking schema changes (`DROP TABLE`, `DROP COLUMN`) in SQL files.
- **LLM Prompt Radar**: Native detection for prompt injections in LLM calls (unsafe f-string concatenation).
- **Semantic Version Bumper**: Automatically parses `git log` and bumps semantic versions based on conventional commits.
- **Discord Webhooks**: Post beautiful CI summary payloads directly to your team's Discord channel.
- **Supply Chain Vulnerability Scanner**: Zero-dependency offline detection of known CVEs in your `requirements.txt` and `package.json`.
- **Infrastructure as Code (IaC) Security**: Detects severe security anti-patterns in Dockerfiles, `docker-compose.yml`, and Terraform files.
- **Code Duplication Detector**: AST-based analysis to find structural duplicate code across your codebase.
- **Cloud Cost Estimator**: Parses your IaC changes to estimate monthly AWS/GCP bill increases before you deploy.
- **Automated Load Tester**: Blasts your URLs with concurrent requests to measure latency regressions.

## Installation

```bash
pip install ciforge-cli
```

## Usage

**Run locally and print to terminal:**
```bash
ciforge --repo . --base-ref origin/main --format markdown --fail-on high
```

**Generate a beautiful HTML dashboard:**
```bash
ciforge --repo . --format html --badge
```

**Run the auto-fixer:**
```bash
ciforge --repo . --fix
```

**Generate a CHANGELOG.md:**
```bash
ciforge --repo . --changelog
```

**Check for config drift:**
```bash
ciforge --repo . --drift
```

**Run deployment health check:**
```bash
ciforge --repo . --deploy-check https://your-production-url.com
```

**Generate architecture diagram:**
```bash
ciforge --repo . --arch-diagram
```

**Auto-generate PR description:**
```bash
ciforge --repo . --pr-describe
```

**Find highly-coupled files (Blast Radius):**
```bash
ciforge --repo . --blast-radius
```

**Scan MCP server configuration:**
```bash
ciforge --repo . --mcp-scan
```

**Detect breaking DB schema changes:**
```bash
ciforge --repo . --schema-scan
```

**Scan for LLM prompt injections:**
```bash
ciforge --repo . --prompt-scan
```

**Auto-bump semantic version based on commits:**
```bash
ciforge --repo . --bump-version
```

**Send CI summary to Discord webhook:**
```bash
ciforge --repo . --discord-webhook https://discord.com/api/webhooks/...
```

**Scan for Supply Chain Vulnerabilities (CVEs):**
```bash
ciforge --repo . --vuln-scan
```

**Scan Infrastructure as Code for Security Issues:**
```bash
ciforge --repo . --iac-scan
```

**Find structural code duplication:**
```bash
ciforge --repo . --dupe-scan
```

**Estimate AWS/GCP Cloud Costs from Terraform:**
```bash
ciforge --repo . --cloud-cost
```

**Run Automated Load Test:**
```bash
ciforge --repo . --load-test https://your-staging-url.com
```

**Install local pre-commit hook (blocks bad commits):**
```bash
ciforge --install-hook
```

## GitHub Action Usage

Use `ciforge` directly in your workflows to comment on PRs and enforce standards:

```yaml
steps:
  - uses: actions/checkout@v4
  - name: Run CI Forge
    uses: Tahiram32/ciforge@v4.0.0
    with:
      repo: '.'
      base-ref: 'origin/main'
      format: 'markdown'
      fail-on: 'high'
      post-comment: 'true'
      badge: 'true'
      openai-key: ${{ secrets.OPENAI_API_KEY }} # Optional: enables AI Reviewer
```

## ❤️ Sponsorship & Commercial Licenses

`ciforge` is licensed under the strict **GNU AGPLv3** license. It is 100% free and open source for individual developers and open-source projects.

### Commercial Dual License
If your company wants to use `ciforge` in a proprietary or closed-source commercial product without being bound by the AGPLv3 restrictions (the "cloud loophole"), you must purchase a Commercial License by sponsoring the project.

[![Sponsor ciforge](https://img.shields.io/badge/Sponsor%20ciforge-%E2%9D%A4-ea4aaa?logo=github-sponsors&style=for-the-badge)](https://github.com/sponsors/Tahiram32)

Every commercial sponsor helps fund:
- 🚀 New features and integrations
- 🐛 Bug fixes and maintenance
- 📖 Documentation and examples
- 🔒 Security research and improvements
