# Tests

The tests cover account and player storage, startup checks, launcher safety, room behavior, PvE setup, and related emulator code. CI runs on Windows with Python 3.12 and 3.14.

From the repository root, install the project and test dependencies, then run:

```powershell
python -m pip install -r requirements.txt
python -m pip install "pytest>=8,<9"
python -m pytest -v tests
```

To run the same Python syntax compilation check used by CI:

```powershell
python -m compileall -q server tools tests
```

Some tests use fixtures and do not require a live Assault Fire client or dedicated server. Check an individual test before assuming it exercises a live client.

See the [main README](../README.md) for supported game files and the [CI workflow](../.github/workflows/ci.yml) for the authoritative test matrix.
