# Tools

Helper scripts are grouped by purpose:

| Folder | Purpose |
| --- | --- |
| [setup](setup/README.md) | Generate local RSA files, configure hosts, and prepare the console |
| [patches](patches/README.md) | Diagnose client files and perform supported compatibility/launch operations |
| [bridge](bridge/README.md) | Dedicated-server UDP bridge |
| [server_spawner](server_spawner/README.md) | Start and supervise the local AFDEV process |
| [research](research/README.md) | Version-specific protocol and symbol research data |

Run commands from the repository root unless a tool explicitly says otherwise. Follow the [main README](../README.md) and [documentation index](../docs/README.md) for the supported workflow.

Only use tools with the verified Assault Fire PH v1.0.0.24 build. Stop when a validation reports an unknown file or signature; do not force patches.
