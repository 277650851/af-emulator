# First-run setup helpers

This folder contains setup utilities used by the main launcher and manual setup path:

- `generate_local_rsa_keypair.py` creates the local server key and matching client configuration.
- `setup_assaultfire_hosts.ps1` applies or repairs the local emulator host mappings.
- `af_console_nonblocking.ps1` supports the launcher's console behavior.

Use the [main README](../../README.md) for the right order and exact commands. Keep `server/PRIVATE.PEM` private. Never upload it, commit it, or send it in a support request.
