"""
Data Fabric client for the MarketPulse worker — shells out to the official
`uip df` CLI rather than hand-rolled REST calls. The CLI's endpoints and auth
are maintained by UiPath and already verified to work in this project (you
used `uip df entities create` directly to set up the entity); reimplementing
the same calls as raw HTTP requests risks guessing wrong endpoint paths.

Requires, before this runs:
    uip login --client-id <ID> --client-secret <SECRET> --tenant <TENANT> --output json
    uip tools install @uipath/data-fabric-tool

Required environment variable:
    DF_ENTITY_ID   the MarketPulseSnapshot entity's GUID
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


def get_first_record_id() -> str | None:
    """Return the id of the (single) snapshot row, or None if the entity is empty."""
    entity_id = os.environ["DF_ENTITY_ID"]
    result = _run_uip("df", "records", "list", entity_id, "--limit", "1")
    # Documented response shape: { TotalCount, Records, HasNextPage, ... }
    records = result.get("Records") or []
    if not records:
        return None
    return records[0]["Id"]


def upsert_snapshot(record: dict) -> None:
    """Insert the snapshot row on first run, update it on every run after that."""
    entity_id = os.environ["DF_ENTITY_ID"]
    record_id = get_first_record_id()
    body = {**record, "Id": record_id} if record_id else record
    verb = "update" if record_id else "insert"
    _run_uip("df", "records", verb, entity_id, "--body", json.dumps(body))
