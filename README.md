# ciforge

[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-ea4aaa?logo=github-sponsors)](https://github.com/sponsors/Tahiram32)
[![PyPI](https://img.shields.io/pypi/v/ciforge-cli)](https://pypi.org/project/ciforge-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/Tahiram32/ciforge/blob/master/LICENSE)

**ciforge** is a zero-dependency CLI and GitHub Action that replaces 20 CI services with one robust tool. Run your complete CI pipeline 100% locally or natively within your actions, faster and with zero external dependencies.

## Features

- **Code Quality**: Intelligent linting and AST-based complexity analysis (cyclomatic complexity, long functions).
- **Test Coverage Analysis**: Deep inspection of test coverage gaps.
- **Secret Detection**: Catch hardcoded credentials before they reach your repository.
- **Config Validation**: Native parsing and validation for JSON, YAML, ENV, TOML, and XML files.
- **PR Metrics & Velocity Tracking**: Analyze pull request size, churn, and time span metrics.
- **AI Reviewer**: Integrates with OpenAI to automatically find logic flaws and missing edge cases.
- **Localization Sync**: Finds missing translation keys by comparing localization files against a base en.json.
- **Git Hooks Installer**: Easily install pre-commit hooks to run ciforge before committing.
- **Auto-Generated Badges**: Generate dynamic SVG badges reflecting repository health.
- **HTML Reports**: Export beautiful standalone HTML reports.
- **Contributor Welcome Module**: Automatically greet first-time contributors.
- **Auto-Fixer (`--fix`)**: Automatically resolves low-hanging issues like debug statements and bad formatting.
- **Custom Ignore Rules**: Whitelist files and dummy secrets via `.ciforge-ignore`.

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
    uses: Tahiram32/ciforge@v1.0.0
    with:
      repo: '.'
      base-ref: 'origin/main'
      format: 'markdown'
      fail-on: 'high'
      post-comment: 'true'
      badge: 'true'
      openai-key: ${{ secrets.OPENAI_API_KEY }} # Optional: enables AI Reviewer
```

## ❤️ Sponsorship

ciforge is free and open source, and will always stay that way. If it saves you time or money by replacing paid CI services, consider sponsoring its continued development!

[![Sponsor ciforge](https://img.shields.io/badge/Sponsor%20ciforge-%E2%9D%A4-ea4aaa?logo=github-sponsors&style=for-the-badge)](https://github.com/sponsors/Tahiram32)

Every sponsor helps fund:
- 🚀 New features and integrations
- 🐛 Bug fixes and maintenance
- 📖 Documentation and examples
- 🔒 Security research and improvements
