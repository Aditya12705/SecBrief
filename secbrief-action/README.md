# SecBrief GitHub Action

Automatically scans pull requests for vulnerabilities with plain-English briefings and compliance mapping.

## Quick Start

Add this to your workflow file (`.github/workflows/secbrief.yml`):

```yaml
name: SecBrief Security Scan
on:
  pull_request:
    types: [opened, synchronize, reopened]
jobs:
  secbrief:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: SecBrief Scan
        uses: your-org/secbrief-action@v1
        with:
          api-key: ${{ secrets.SECBRIEF_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

| Name | Description | Required | Default |
|------|-------------|----------|---------|
| `api-key` | Your SecBrief API key from secbrief.dev/signup | ✅ | - |
| `github-token` | GitHub token for posting PR comments | ✅ | `${{ github.token }}` |
| `fail-on-severity` | Minimum severity to fail the check (critical, high, medium, low) | ❌ | critical |
| `secbrief-api-url` | SecBrief API base URL. Override for self-hosted. | ❌ | https://api.secbrief.dev |

## Getting an API Key

Get your free API key at [secbrief.dev/signup](https://secbrief.dev/signup).

## Example PR Comment

🔴 **Critical severity** found! SecBrief will post a nicely formatted comment with:
- Severity badges
- Plain-English explanations
- OWASP/CWE tags
- Fix recommendations
- Compliance mapping

## License

MIT
