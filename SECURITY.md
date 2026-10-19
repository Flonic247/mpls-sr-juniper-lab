# Security policy

This repository contains lab material only. It must never contain real credentials or production data.

## What was removed from the published configurations

Root password hashes and VM-specific identifiers. See [configs/SANITIZATION.md](configs/SANITIZATION.md). `python3 tools/audit.py` fails its `Secrets` check if a password hash or VM identifier reappears.

## If you find sensitive data

Open a private security advisory on the repository (or contact the maintainer at `+2347038185610`) instead of a public issue. Include the file and line, not the secret itself.

## Guidance for users and contributors

- Set your own root password when loading the configurations; never reuse a production password.
- Do not paste production configurations here. Replace secrets with placeholders such as `$9$REDACTED`.
- The lab addresses are private or RFC 5737 documentation ranges. Do not connect the lab to production networks.
- Use `commit confirmed` when experimenting.
