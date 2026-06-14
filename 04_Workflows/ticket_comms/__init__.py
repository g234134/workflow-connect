"""Minimal ticket state-change customer comms (WC-T2).

Generates structured communication payloads when Multi-Chat ticket STATE
changes, and dispatches via pluggable send adapters (file/log stub by default).
"""

from ticket_comms.message_generator import (
    SCHEMA_VERSION,
    build_comms_payload,
    compute_state_diff,
    snapshot_from_ticket_record,
)
from ticket_comms.order_events import (
    build_order_comms_payload,
    emit_order_comms,
)
from ticket_comms.sender import CommsSender, FileLogSender, NullSender
from ticket_comms.transition import emit_ticket_comms_on_change

__all__ = [
    "SCHEMA_VERSION",
    "CommsSender",
    "FileLogSender",
    "NullSender",
    "build_comms_payload",
    "build_order_comms_payload",
    "compute_state_diff",
    "emit_order_comms",
    "emit_ticket_comms_on_change",
    "snapshot_from_ticket_record",
]
