"""
Storage client for the MarketPulse worker — reads/writes a single Orchestrator
Text asset via the `uip or assets` CLI.

This replaced an earlier Data Fabric-based implementation: Data Fabric's
record-level API rejected the confidential/client-credentials app identity
with "unsupported robot type" in every configuration tested (correct scopes,
correct entity permissions, IP restriction confirmed disabled) — a platform
behavior specific to Data Fabric, confirmed by testing rather than assumed.
The exact same identity was confirmed, by direct testing, to work fine
against Orchestrator Assets — so the whole snapshot is now stored as a single
JSON blob in one Text asset instead of a Data Fabric entity row.

Required environment variables:
    ASSET_FOLDER_PATH   e.g. "Shared" — the Orchestrator folder the asset lives in
    ASSET_KEY           the MarketPulseSnapshot asset's UUID (not its name —
                         update/get-asset-value both require the key)
"""
import json
import os
import subprocess


def _run_uip(*args: str) -> dict:
    """Run a `uip` CLI command and parse its --output json result.

    Raises RuntimeError with the full stdout+stderr on any non-zero exit or
    non-JSON output, so failures are visible in the GitHub Actions log
    instead of silently returning something unexpected.
    """
    cmd = ["uip", *args, "--output", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Non-JSON output from: {' '.join(cmd)}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        ) from e


def upsert_snapshot(record: dict) -> None:
    """Overwrite the single MarketPulseSnapshot asset with the latest snapshot."""
    asset_key = os.environ["ASSET_KEY"]
    _run_uip("or", "assets", "update", asset_key, json.dumps(record))


def get_snapshot() -> dict | None:
    """Read the current snapshot back (used for local/manual verification, not
    required by the worker's write path — upsert_snapshot always overwrites)."""
    asset_key = os.environ["ASSET_KEY"]
    folder_path = os.environ["ASSET_FOLDER_PATH"]
    result = _run_uip("or", "assets", "get-asset-value", asset_key, "--folder-path", folder_path)
    value = result.get("Data", {}).get("StringValue") or result.get("Data", {}).get("Value")
    if not value:
        return None
    return json.loads(value)


