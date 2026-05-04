# Security Rules

## Never in source code or committed files
- Hardcoded API keys, tokens, passwords
- Hardcoded internal IPs or URLs (use config)
- `eval()`/`exec()` with user input
- SQL string concatenation (use parameterized queries)
- Disabled SSL verification without explicit justification

## Secrets go in
- Environment variables or `.env` files (gitignored)
- Never in `settings.json`, `*.pem`, `*.key`, `credentials.json`

## If a token is accidentally committed
1. Rotate the token immediately
2. Remove from history with BFG or `git filter-branch`
3. Force push; verify old token is invalid

Note: `security-guard.js` pre-tool hook automatically checks writes/edits for secrets.
