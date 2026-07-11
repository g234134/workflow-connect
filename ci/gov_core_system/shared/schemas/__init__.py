"""JSON schema documents for gov_core shared contracts."""

from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent

ERROR_SCHEMA = SCHEMA_DIR / "error_schema.json"
LANGFUSE_METADATA_SCHEMA = SCHEMA_DIR / "langfuse_metadata.json"
TASK_COSTS_SCHEMA = SCHEMA_DIR / "task_costs.json"
BUDGET_CONFIG_SCHEMA = SCHEMA_DIR / "budget_config.json"
CHECKPOINT_STATE_SCHEMA = SCHEMA_DIR / "checkpoint_state.json"
DLQ_RECORD_SCHEMA = SCHEMA_DIR / "dlq_record.json"
FEATURE_FLAGS_SCHEMA = SCHEMA_DIR / "feature_flags.json"
ALERT_EVENT_V1_SCHEMA = SCHEMA_DIR / "alert_event_v1.json"
PHASE5_DASHBOARD_API_V1_SCHEMA = SCHEMA_DIR / "phase5_dashboard_api_v1.json"
SECURITY_SANITIZE_V1_SCHEMA = SCHEMA_DIR / "security_sanitize_v1.json"
PHASE6_5_ENTITIES_V1_SCHEMA = SCHEMA_DIR / "phase6_5_entities_v1.json"
PHASE6_5_EVENTS_V1_SCHEMA = SCHEMA_DIR / "phase6_5_events_v1.json"
INTAKE_GATE_V1_SCHEMA = SCHEMA_DIR / "intake_gate_v1.json"
INTAKE_SCHEMA_V1_SCHEMA = SCHEMA_DIR / "intake_schema_v1.json"
TOOL_CATALOG_V1_SCHEMA = SCHEMA_DIR / "tool_catalog_v1.json"
TOOL_DECISION_LOG_V1_SCHEMA = SCHEMA_DIR / "tool_decision_log_v1.json"
REPO_TOOL_CATALOG_V1_SCHEMA = SCHEMA_DIR / "repo_tool_catalog_v1.json"
ENVELOPE_V2_SCHEMA = SCHEMA_DIR / "envelope_v2.json"
