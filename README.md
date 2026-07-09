# ciforge

**ciforge** is a zero-dependency CLI and GitHub Action that replaces 20 CI services with one robust tool. Run your complete CI pipeline 100% locally or natively within your actions, faster and with zero external dependencies.

## Features

- **Code Quality**: Intelligent linting and AST-based complexity analysis (cyclomatic complexity, long functions).
- **Test Coverage Analysis**: Deep inspection of test coverage gaps.
- **Secret Detection**: Catch hardcoded credentials before they reach your repository.
- **Config Validation**: Ensure your CI/CD and infrastructure configuration files are sound.
- **PR Metrics & Velocity Tracking**: Analyze pull request size, churn, and time span metrics.
- **AI Reviewer**: Integrates with OpenAI to automatically find logic flaws and missing edge cases.
- **Localization Sync**: Finds missing translation keys by comparing localization files against a base en.json.
- **Git Hooks Installer**: Easily install pre-commit hooks to run ciforge before committing.
- **Auto-Generated Badges**: Generate dynamic SVG badges reflecting repository health.
- **HTML Reports**: Export beautiful standalone HTML reports.
- **Contributor Welcome Module**: Automatically greet first-time contributors.

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
    uses: Tahiram32/ciforge@v0.3.1
    with:
      repo: '.'
      base-ref: 'origin/main'
      format: 'markdown'
      fail-on: 'high'
      post-comment: 'true'
      badge: 'true'
      openai-key: ${{ secrets.OPENAI_API_KEY }} # Optional: enables AI Reviewer
```

## Roadmap (v1.0.0)
We are actively working towards General Availability! Check our [Milestones](https://github.com/Tahiram32/ciforge/milestones) for progress on:
- 🧰 **Auto-Fixer (`--fix`)**: Automatically resolve low-hanging issues.
- 🛡️ **Custom Ignore Rules**: Support for `.ciforge-ignore` whitelists.
- ⚙️ **Expanded Validation**: Native parsing for TOML and XML files.
