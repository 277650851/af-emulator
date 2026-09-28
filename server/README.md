# Server package

This folder contains the emulator backend. The main entry point is `assaultfire_server_v143b.py`; the other modules provide account and player persistence, authentication, startup checks, room management, dedicated-server spawning, logging, and local AP synchronization.

## Run it

Follow the [main README](../README.md) and run commands from the repository root. The documented one-click launcher is the normal player path. Developers who need backend listeners without a local game client can use the documented `--server-only` option; it deliberately does not unlock local game launch helpers.

## Data and secrets

- Keep `PRIVATE.PEM` private. Never commit or share it.
- Treat SQLite databases, logs, and account data as local runtime data.
- Do not put proprietary game files in this repository.

See [Architecture](../docs/ARCHITECTURE.md), [Project Status](../docs/STATUS.md), and [PvE Runtime](../docs/PVE_RUNTIME.md) for current behavior.
