"""Order ledger storage backends (WC-T4 v0.1)."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from order_ledger.models import OrderRecord


class OrderLedgerStore(ABC):
    """Abstract store for order intake records."""

    @abstractmethod
    def get_by_order_id(self, order_id: str) -> OrderRecord | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_ticket_id(self, ticket_id: str) -> OrderRecord | None:
        raise NotImplementedError

    @abstractmethod
    def list_orders(self) -> list[OrderRecord]:
        raise NotImplementedError

    @abstractmethod
    def put(self, order: OrderRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def update(self, order: OrderRecord) -> None:
        """Persist an updated order record (e.g. status transition)."""
        raise NotImplementedError


class InMemoryOrderLedgerStore(OrderLedgerStore):
    """In-process store keyed by order_id and ticket_id."""

    def __init__(self) -> None:
        self._by_order_id: dict[str, OrderRecord] = {}
        self._by_ticket_id: dict[str, OrderRecord] = {}

    def get_by_order_id(self, order_id: str) -> OrderRecord | None:
        return self._by_order_id.get(order_id)

    def get_by_ticket_id(self, ticket_id: str) -> OrderRecord | None:
        return self._by_ticket_id.get(ticket_id)

    def list_orders(self) -> list[OrderRecord]:
        return sorted(self._by_order_id.values(), key=lambda o: o.created_at)

    def put(self, order: OrderRecord) -> None:
        self._by_order_id[order.order_id] = order
        self._by_ticket_id[order.ticket_id] = order

    def update(self, order: OrderRecord) -> None:
        self._by_order_id[order.order_id] = order
        self._by_ticket_id[order.ticket_id] = order


class JsonlFileStore(OrderLedgerStore):
    """Append-only JSONL file with in-memory index (reload on init)."""

    def __init__(self, jsonl_path: str | Path) -> None:
        self.jsonl_path = Path(jsonl_path)
        self._memory = InMemoryOrderLedgerStore()
        self._load_existing()

    def _load_existing(self) -> None:
        if not self.jsonl_path.is_file():
            return
        for line in self.jsonl_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            record = OrderRecord.from_dict(raw)
            self._memory.update(record)

    def get_by_order_id(self, order_id: str) -> OrderRecord | None:
        return self._memory.get_by_order_id(order_id)

    def get_by_ticket_id(self, ticket_id: str) -> OrderRecord | None:
        return self._memory.get_by_ticket_id(ticket_id)

    def list_orders(self) -> list[OrderRecord]:
        return self._memory.list_orders()

    def put(self, order: OrderRecord) -> None:
        existing = self._memory.get_by_ticket_id(order.ticket_id)
        if existing is not None:
            return
        self._append_line(order)
        self._memory.put(order)

    def update(self, order: OrderRecord) -> None:
        if self._memory.get_by_order_id(order.order_id) is None:
            raise KeyError(f"order_not_found:{order.order_id}")
        self._append_line(order)
        self._memory.update(order)

    def _append_line(self, order: OrderRecord) -> None:
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = order.to_dict()
        with self.jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
