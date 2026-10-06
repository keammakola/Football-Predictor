# Security reporting

Do not post API keys, credential files or exploit details in public issues.
Use GitHub's private vulnerability reporting for this repository if available;
otherwise contact the maintainer through https://keabetswe.online to arrange a
private report.

Include the affected commit, reproduction steps and impact, with secrets
redacted. If a credential is exposed, revoke it with its provider first; removing
it from the current file does not remove it from Git history.

The historical website requires no API credentials. Optional research tools
read keys from environment variables or ignored local configuration. Dependency
checks and tests are safeguards, not a full security audit or a warranty.
