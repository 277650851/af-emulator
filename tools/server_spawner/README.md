# Dedicated-server spawner

This folder contains the AFDEV loader used by the emulator to start dedicated-server instances for PvE matches.

The emulator's server-side lifecycle controls allocation and launch. Normal players should not start the loader manually; use the [main README](../../README.md). Developers can read [PvE Runtime](../../docs/PVE_RUNTIME.md) and [PvE Bridge and Spawner](../../docs/PVE_BRIDGE_AND_SPAWNER.md) for the configured flow and troubleshooting context.

The launcher creates its local AFDEV executable from the user's own verified game files. Do not add or redistribute proprietary game binaries here.
