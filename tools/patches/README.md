# Client diagnostics and launch helpers

This folder contains tools for checking the client files and performing the supported TCLS/TGame compatibility steps.

- `diagnose_tcls_apclient.py` checks the local TCLS and APClient setup.
- `patch_tcls_apclient_raw_pem.py` applies the known TCLS compatibility patch when its input matches the supported build.
- `patch_tcls_suspended_launch.py` coordinates the safe manual TCLS-to-TGame handoff.
- `patch_tgame_datetime.py` and `tgame_binary.py` support the verified TGame compatibility workflow.
- `launch_preflight_gate.py` enforces the local launch gate.

The one-click `START_ASSAULT_FIRE.ps1` path is the normal player workflow. It verifies the datetime patch site, saves an exact `TGame.exe.bak`, applies a position-independent permanent patch when a safe executable-section code cave exists, then verifies the installed image. Unknown signatures, conflicting backups, and missing/ambiguous caves fail without overwriting TGame. For manual setup, follow the exact steps in the [main README](../../README.md). When using the suspended-launch helper, do not also run the datetime patch separately.
