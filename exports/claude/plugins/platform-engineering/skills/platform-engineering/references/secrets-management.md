# Secrets Management

## MUST

- **Never store API keys, database credentials, private keys, or any secret in frontend code, client-side bundles, or mobile app binaries.** They will be extracted.
  - GitHub detected over 39 million leaked secrets across its platform in 2024.
  - GitGuardian found 12.8 million secrets in public repositories in 2023 alone, a 28% year-over-year increase.
  - A Wiz study found 65% of Forbes AI 50 companies had leaked verified secrets on GitHub, including Hugging Face tokens that could have exposed approximately 1,000 private AI models.

- **Never commit secrets to version control.** Use `.gitignore` for `.env` files and implement pre-commit hooks with tools like detect-secrets, GitLeaks, or TruffleHog. Enable GitHub's push protection and secret scanning.

- **Use environment variables or dedicated secret management services** (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, GCP Secret Manager) for server-side secrets. For third-party API calls requiring keys, proxy through your backend -- never call external APIs with secrets directly from the client.

## DON'T

- Store secrets in `.env` files that get bundled into client builds. Variables prefixed with `REACT_APP_`, `VITE_`, or `NEXT_PUBLIC_` are embedded in the production JavaScript bundle and are visible to anyone who opens DevTools.
- Hardcode secrets in mobile binaries -- reverse-engineering tools extract them in minutes.
- Store secrets in Electron ASAR archives, which are extractable with `asar extract app.asar`.

## Official docs

- OWASP Secrets Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- AWS Secrets Manager: https://aws.amazon.com/secrets-manager/
- HashiCorp Vault: https://www.vaultproject.io/
- Azure Key Vault: https://azure.microsoft.com/en-us/products/key-vault
- GCP Secret Manager: https://cloud.google.com/security/products/secret-manager
- GitHub secret scanning + push protection: https://docs.github.com/en/code-security/secret-scanning
- detect-secrets: https://github.com/Yelp/detect-secrets
- GitLeaks: https://github.com/gitleaks/gitleaks
- TruffleHog: https://github.com/trufflesecurity/trufflehog
