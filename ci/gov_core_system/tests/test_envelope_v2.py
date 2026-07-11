"""Wave 6 envelope v2 contract and writer tests."""

from __future__ import annotations

import json
import unittest

from pydantic import ValidationError

from core.envelope_writer import (
    SKU_BASIC,
    SKU_ENRICH,
    EnvelopeWriterError,
    build_envelope,
    write_envelopes,
)
from core.schemas.envelope_v2 import (
    BasicEnvelopeV2,
    ENRICHMENT_V0_1_SCHEMA_VERSION,
    ENVELOPE_V2_SCHEMA_VERSION,
    EnrichEnvelopeV2,
)
from shared.schemas import ENVELOPE_V2_SCHEMA

SHA_A = "a" * 64
SHA_B = "b" * 64


def _base_payload(*, sha: str = SHA_A, clean_status: str = "ok") -> dict:
    return {
        "file_id": "file-001",
        "content_sha256": sha,
        "clean_status": clean_status,
        "name": "demo.py",
        "extension": ".py",
        "original_type": "python_source",
        "size_bytes": 123,
        "encoding": "utf-8",
        "stored_logical_path": "cleaned_full/demo.py.json",
        "content_summary": {
            "line_count": 12,
            "char_count": 240,
            "imports": ["json", "pathlib"],
            "preview_lines": ["import json", "from pathlib import Path"],
        },
        "groq_used": False,
        "groq_reason": None,
        "parse_strategy": "ast",
        "warnings": [],
    }


def _present_enrichment(*, used_llm: bool = False) -> dict:
    return {
        "schema_version": ENRICHMENT_V0_1_SCHEMA_VERSION,
        "present": True,
        "detected_language": "en",
        "domain_tags": ["python", "backend"],
        "content_kind": "code",
        "quality_score": 91,
        "review_priority": "low",
        "enrichment_provenance": "llm" if used_llm else "rules",
        "signals": {
            "has_parse_warnings": False,
            "used_llm": used_llm,
            "line_count": 12,
            "import_count": 2,
        },
    }


class EnvelopeV2Tests(unittest.TestCase):
    def test_basic_valid_no_enrichment_key(self) -> None:
        model = build_envelope({"sku": SKU_BASIC}, _base_payload())
        self.assertIsInstance(model, BasicEnvelopeV2)
        dumped = model.to_dict()
        self.assertEqual(dumped["schema_version"], ENVELOPE_V2_SCHEMA_VERSION)
        self.assertFalse(dumped["groq_used"])
        self.assertNotIn("enrichment", dumped)

    def test_enrich_valid_present_true(self) -> None:
        payload = _base_payload(sha=SHA_B)
        payload["groq_used"] = True
        payload["groq_reason"] = "llm_assist_requested"
        payload["enrichment"] = _present_enrichment(used_llm=True)
        model = build_envelope({"sku": SKU_ENRICH}, payload)
        self.assertIsInstance(model, EnrichEnvelopeV2)
        self.assertTrue(model.enrichment.present)
        self.assertEqual(model.enrichment.quality_score, 91)
        self.assertEqual(model.enrichment.review_priority, "low")

    def test_enrich_present_false_allowed_for_non_ok_row(self) -> None:
        payload = _base_payload(clean_status="rejected")
        payload["enrichment"] = {
            "schema_version": ENRICHMENT_V0_1_SCHEMA_VERSION,
            "present": False,
            "domain_tags": [],
            "quality_score": None,
            "review_priority": None,
            "detected_language": None,
            "content_kind": None,
            "enrichment_provenance": None,
            "signals": None,
        }
        model = build_envelope({"sku": SKU_ENRICH}, payload)
        self.assertIsInstance(model, EnrichEnvelopeV2)
        self.assertFalse(model.enrichment.present)
        self.assertIsNone(model.enrichment.quality_score)
        self.assertIsNone(model.enrichment.review_priority)

    def test_enrich_ok_with_present_false_rejected(self) -> None:
        payload = _base_payload()
        payload["enrichment"] = {
            "schema_version": ENRICHMENT_V0_1_SCHEMA_VERSION,
            "present": False,
            "domain_tags": [],
            "quality_score": None,
            "review_priority": None,
            "detected_language": None,
            "content_kind": None,
            "enrichment_provenance": None,
            "signals": None,
        }
        with self.assertRaises(ValidationError):
            build_envelope({"sku": SKU_ENRICH}, payload)

    def test_path_leak_rejected(self) -> None:
        payload = _base_payload()
        payload["stored_logical_path"] = r"D:\leaky\demo.py.json"
        with self.assertRaises(ValidationError):
            build_envelope({"sku": SKU_BASIC}, payload)

    def test_billable_fields_rejected(self) -> None:
        payload = _base_payload()
        payload["billable_u"] = 1
        with self.assertRaises(EnvelopeWriterError):
            build_envelope({"sku": SKU_BASIC}, payload)

    def test_delivery_raw_path_fields_rejected(self) -> None:
        payload = _base_payload()
        payload["source_path"] = "raw_inbound/demo.py"
        with self.assertRaises(EnvelopeWriterError):
            build_envelope({"sku": SKU_BASIC}, payload)

    def test_write_envelopes_returns_dicts(self) -> None:
        out = write_envelopes({"sku": SKU_BASIC}, [_base_payload()])
        self.assertEqual(len(out), 1)
        self.assertIsInstance(out[0], dict)
        self.assertNotIn("enrichment", out[0])

    def test_schema_file_exists_and_declares_basic_enrich_branches(self) -> None:
        self.assertTrue(ENVELOPE_V2_SCHEMA.is_file(), str(ENVELOPE_V2_SCHEMA))
        data = json.loads(ENVELOPE_V2_SCHEMA.read_text(encoding="utf-8"))
        titles = [branch["title"] for branch in data["oneOf"]]
        self.assertEqual(titles, ["BASIC", "ENRICH"])


if __name__ == "__main__":
    unittest.main()
