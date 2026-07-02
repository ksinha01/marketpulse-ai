# Data Fabric Entity: MarketPulseSnapshot

## Create it in one command

Requires the Data Fabric CLI tool: `uip tools install @uipath/data-fabric-tool`
(and `uip login status --output json` first — see the platform skill if not
logged in).

```bash
uip df entities create "MarketPulseSnapshot" \
  --body '{
    "displayName": "MarketPulse Snapshot",
    "description": "Latest MarketPulse worker refresh cycle",
    "fields": [
      {"fieldName": "Sentiment",            "type": "STRING",           "lengthLimit": 50},
      {"fieldName": "Score",                "type": "INTEGER"},
      {"fieldName": "DecisionText",         "type": "STRING",           "lengthLimit": 500},
      {"fieldName": "PredictionTrend",      "type": "STRING",           "lengthLimit": 50},
      {"fieldName": "PredictionConfidence", "type": "STRING",           "lengthLimit": 50},
      {"fieldName": "AlertType",            "type": "STRING",           "lengthLimit": 50},
      {"fieldName": "AlertMessage",         "type": "MULTILINE_TEXT",   "lengthLimit": 2000},
      {"fieldName": "AlertAction",          "type": "STRING",           "lengthLimit": 500},
      {"fieldName": "StrategyConfidence",   "type": "STRING",           "lengthLimit": 50},
      {"fieldName": "Pcr",                  "type": "DECIMAL",          "decimalPrecision": 4},
      {"fieldName": "MaxPain",              "type": "DECIMAL",          "decimalPrecision": 2},
      {"fieldName": "TradeType",            "type": "STRING",           "lengthLimit": 50},
      {"fieldName": "TradeReason",          "type": "MULTILINE_TEXT",   "lengthLimit": 2000},
      {"fieldName": "MarketJson",           "type": "MULTILINE_TEXT",   "lengthLimit": 10000},
      {"fieldName": "SectorsJson",          "type": "MULTILINE_TEXT",   "lengthLimit": 10000},
      {"fieldName": "NewsJson",             "type": "MULTILINE_TEXT",   "lengthLimit": 10000},
      {"fieldName": "ChecklistJson",        "type": "MULTILINE_TEXT",   "lengthLimit": 10000},
      {"fieldName": "OptionsJson",          "type": "MULTILINE_TEXT",   "lengthLimit": 10000},
      {"fieldName": "StrategyJson",         "type": "MULTILINE_TEXT",   "lengthLimit": 10000},
      {"fieldName": "InsightText",          "type": "MULTILINE_TEXT",   "lengthLimit": 2000},
      {"fieldName": "SnapshotTime",         "type": "DATETIME_WITH_TZ"}
    ]
  }' \
  --output json
```

The response looks like `{ "Result": "Success", "Code": "EntityCreated", "Data": { "Id": "<entity-id>" } }`
— that `ID` is the `DF_ENTITY_ID` value both `worker/.env.production` and
`webapp/.env` need. Capture it directly instead of copy-pasting by hand:

```bash
ENTITY_ID=$(uip df entities create "MarketPulseSnapshot" --body @entity-body.json --output json | python3 -c "import sys,json; print(json.load(sys.stdin)['Data']['Id'])")
echo "$ENTITY_ID"
```

(Save the JSON body above to `entity-body.json` first if you use the `@file`
form — handy since the payload is long.) `MULTILINE_TEXT` caps out at
`lengthLimit: 10000`; if a market snapshot ever serializes larger than that
(e.g. very large news arrays), either raise the source data limits in
`worker/app/worker.py` or split that field across two columns — the CLI will
reject inserts that exceed the field's `lengthLimit`.

Verify it after creation:

```bash
uip df entities get "$ENTITY_ID" --output json
```

---

## Manual reference (if you prefer the UI)

| Field Name        | Type              | Notes                                        |
|--------------------|------------------|-----------------------------------------------|
| Sentiment           | TEXT             | e.g. "BULLISH", "BEARISH", "NEUTRAL"          |
| Score               | INTEGER          | sentiment score                               |
| DecisionText        | TEXT             | final_decision() output                       |
| PredictionTrend     | TEXT             | "UP" / "DOWN" / "SIDEWAYS"                    |
| PredictionConfidence| TEXT             |                                                |
| AlertType           | TEXT             |                                                |
| AlertMessage        | MULTILINE_TEXT   |                                                |
| AlertAction         | TEXT             |                                                |
| StrategyConfidence  | TEXT             |                                                |
| Pcr                 | DECIMAL          |                                                |
| MaxPain             | DECIMAL          |                                                |
| TradeType           | TEXT             | "NO TRADE" / "BUY CE" / etc. (signal only)    |
| TradeReason         | MULTILINE_TEXT   |                                                |
| MarketJson          | MULTILINE_TEXT   | full `market` dict, JSON-serialized           |
| SectorsJson         | MULTILINE_TEXT   | JSON-serialized                               |
| NewsJson            | MULTILINE_TEXT   | JSON-serialized (array)                       |
| ChecklistJson       | MULTILINE_TEXT   | JSON-serialized                               |
| OptionsJson         | MULTILINE_TEXT   | JSON-serialized (calls/puts/pcr/max_pain)     |
| StrategyJson        | MULTILINE_TEXT   | JSON-serialized                               |
| InsightText         | MULTILINE_TEXT   |                                                |
| SnapshotTime        | DATETIME_WITH_TZ | custom field the worker sets — do NOT rely on the auto `CreateTime`/`UpdateTime` audit columns for "as of" display |

**Pattern:** the worker always UPSERTS into a single fixed row (keep an `Id` you save
after the first insert, e.g. store it back into an Orchestrator Asset
`MarketPulseSnapshotRowId`) rather than inserting a new row every cycle. If you want
history, instead insert a new row each cycle and have the web app read
`getAllRecords` sorted by `SnapshotTime` descending, `pageSize: 1`.

Record keys are case-sensitive on write — use these exact names.
