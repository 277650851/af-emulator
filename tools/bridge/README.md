# Dedicated-server bridge

This folder contains the UDP bridge used by the emulator's dedicated-server lifecycle. The current implementation supports the configured multi-peer latch path.

The server and spawner manage when the bridge starts and how it routes packets. It is an internal helper; do not launch it directly for normal gameplay. Use the [main README](../../README.md) for player setup and [PvE Runtime](../../docs/PVE_RUNTIME.md) plus [PvE Bridge and Spawner](../../docs/PVE_BRIDGE_AND_SPAWNER.md) for the lifecycle details.

Use the bridge only with the repository's supported Assault Fire PH v1.0.0.24 workflow.
