# ciforge

**ciforge** is a zero-dependency CLI and GitHub Action that replaces 20 CI services with one robust tool. Run your complete CI pipeline 100% locally or natively within your actions, faster and with zero external dependencies.

## Features

- **Code Quality**: Intelligent linting and AST-based complexity analysis (cyclomatic complexity, long functions).
- **Test Coverage Analysis**: Deep inspection of test coverage gaps.
- **Secret Detection**: Catch hardcoded credentials before they reach your repository.
- **Config Validation**: Ensure your CI/CD and infrastructure configuration files are sound.
- **PR Metrics & Velocity Tracking**: Analyze pull request size, churn, and time span metrics.
- **AI Reviewer**: Integrates with OpenAI to automatically find logic flaws and missing edge cases.
- **Image Optimization**: Detects large unoptimized assets (.png, .jpg, .jpeg) over 500KB.
- **Localization Sync**: Finds missing translation keys by comparing localization files against a base en.json.

## Installation

```bash
pip install ciforge
```

## Usage

Run locally:
```bash
ciforge --repo . --base-ref origin/main --format markdown --fail-on high
```

## GitHub Action Usage

Use `ciforge` directly in your workflows:

```yaml
steps:
  - uses: actions/checkout@v3
  - name: Run ciforge
    uses: your-org/ciforge@v0.1.0
    with:
      repo: '.'
      base-ref: 'origin/main'
      format: 'markdown'
      fail-on: 'high'
      post-comment: 'true'
```
