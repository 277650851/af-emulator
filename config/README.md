# Local host configuration

This folder contains the documented host mappings used by the local emulator.

- `hosts.txt` lists the three retired Assault Fire PH hostnames and their local `127.0.0.1` mappings.
- To apply or repair the Windows hosts entries, use [the setup helper](../tools/setup/setup_assaultfire_hosts.ps1) from the repository root.
- To restore normal name resolution, remove or comment out only the emulator mappings. The helper is safer than editing the Windows hosts file by hand.

These mappings send the client to the emulator on the same PC. They do not contact or change the original game services.

See the [main README](../README.md) for setup and launch instructions.
