"""Unit tests for Wave 6 intake gate (W6-IMPL-INTAKE-GATE)."""

from __future__ import annotations

import unittest

from core.schemas.wave6_intake_gate import SUGGESTED_PIPELINE_HINT, WAVE6_INTAKE_GATE_SCHEMA_VERSION
from core.wave6_intake_gate import run_intake_gate


def _accept_basic_payload() -> dict:
    return {
        "description": "raw_inbound 碼源清洗 wave factory cleaned_full envelope",
        "tags": ["raw_inbound", "size_policy:acknowledged"],
        "explicit_task_type": "chariot.factory",
        "product_sku": "CLEAN-BASIC",
        "batch_size_hint": 500,
        "client_ref": "client-wave6-001",
        "file_extension_hints": [".py"],
        "inbound_path_hint": "raw_inbound/batch-42",
    }


class TestWave6IntakeGate(unittest.TestCase):
    def test_accept_explicit_data_cleaning_basic(self) -> None:
        out = run_intake_gate(_accept_basic_payload())
        self.assertTrue(out.ok)
        self.assertEqual(out.decision, "accept")
        self.assertEqual(out.work_category, "data_cleaning")
        self.assertEqual(out.suggested_product_sku, "CLEAN-BASIC")
        self.assertEqual(out.suggested_pipeline, SUGGESTED_PIPELINE_HINT)
        self.assertEqual(out.suggested_task_type, "chariot.factory")
        self.assertEqual(out.schema_version, WAVE6_INTAKE_GATE_SCHEMA_VERSION)
        self.assertEqual(out.defer_fields_needed, [])

        check_ids = {c.id for c in out.gate_checks}
        self.assertIn("PIPELINE-ANCHOR", check_ids)
        self.assertIn("SKU-PRESENT", check_ids)
        self.assertIn("SKU-ENUM", check_ids)
        self.assertIn("ABS-PATH-BAN", check_ids)
        self.assertIn("BASIC-NO-ENRICH", check_ids)

        p65 = out.phase6_5_pre_state
        assert p65 is not None
        order = p65.get("order") or {}
        mapping = order.get("field_mapping") or {}
        self.assertEqual(mapping.get("intake.product_sku"), "order.line_items[0].sku")
        self.assertNotEqual(mapping.get("intake.suggested_pipeline"), "order.line_items[0].sku")

    def test_accept_enrich_with_profile(self) -> None:
        out = run_intake_gate(
            {
                "description": "code_cleaning_pipeline_v2 raw_inbound cleaned_full",
                "tags": ["size_policy:acknowledged"],
                "product_sku": "CLEAN-ENRICH",
                "enrichment_profile": {
                    "risk_scan_level": "metadata_only",
                    "llm_assist": "on_failures_only",
                    "domain_tags": ["python"],
                },
            }
        )
        self.assertEqual(out.decision, "accept")
        self.assertEqual(out.suggested_product_sku, "CLEAN-ENRICH")

    def test_accept_resolves_sku_from_tag_alias(self) -> None:
        out = run_intake_gate(
            {
                "explicit_task_type": "chariot.factory",
                "description": "wave raw_inbound 清洗",
                "tags": ["sku:clean-basic", "size_policy:acknowledged"],
            }
        )
        self.assertEqual(out.decision, "accept")
        self.assertEqual(out.suggested_product_sku, "CLEAN-BASIC")

    def test_defer_missing_product_sku_with_cleaning_signal(self) -> None:
        out = run_intake_gate(
            {
                "description": "raw_inbound wave 清洗 cleaned_full code_cleaning_pipeline_v2",
                "tags": ["碼源"],
            }
        )
        self.assertTrue(out.ok)
        self.assertEqual(out.decision, "defer")
        self.assertIn("product_sku", out.defer_fields_needed)
        self.assertIn("missing_product_sku", out.reasons)

    def test_defer_ambiguous_generic_request(self) -> None:
        out = run_intake_gate({"description": "幫我處理一些檔案"})
        self.assertEqual(out.decision, "defer")
        self.assertTrue(out.defer_fields_needed)

    def test_defer_enrich_requires_llm_or_domain(self) -> None:
        out = run_intake_gate(
            {
                "explicit_task_type": "chariot.factory",
                "description": "raw_inbound enrich wave",
                "tags": ["size_policy:acknowledged"],
                "product_sku": "CLEAN-ENRICH",
                "enrichment_profile": {
                    "risk_scan_level": "none",
                    "llm_assist": "off",
                    "domain_tags": [],
                },
            }
        )
        self.assertEqual(out.decision, "defer")
        self.assertIn("enrich_requires_llm_or_domain", out.reasons)

    def test_defer_sku_tag_conflict(self) -> None:
        out = run_intake_gate(
            {
                "explicit_task_type": "chariot.factory",
                "description": "raw_inbound wave",
                "tags": ["sku:clean-basic", "sku:clean-enrich", "size_policy:acknowledged"],
                "product_sku": "CLEAN-BASIC",
            }
        )
        self.assertEqual(out.decision, "defer")
        self.assertIn("sku_tag_conflict", out.reasons)

    def test_reject_out_of_scope_rag(self) -> None:
        out = run_intake_gate(
            {
                "description": "rag query graphrag ingest_verify document_chunks",
                "product_sku": "CLEAN-BASIC",
            }
        )
        self.assertEqual(out.decision, "reject")
        self.assertTrue(
            "sku_without_cleaning_intent" in out.reasons or "not_data_cleaning" in out.reasons
        )

    def test_reject_absolute_path_hint(self) -> None:
        out = run_intake_gate(
            {
                "explicit_task_type": "chariot.factory",
                "description": "raw_inbound 清洗",
                "product_sku": "CLEAN-BASIC",
                "tags": ["size_policy:acknowledged"],
                "inbound_path_hint": r"D:\project\raw_inbound",
            }
        )
        self.assertEqual(out.decision, "reject")
        self.assertIn("absolute_path_forbidden", out.reasons)

    def test_reject_invalid_product_sku(self) -> None:
        out = run_intake_gate(
            {
                "explicit_task_type": "chariot.factory",
                "description": "raw_inbound wave",
                "tags": ["size_policy:acknowledged"],
                "product_sku": "CLEAN-ULTIMATE",
            }
        )
        self.assertEqual(out.decision, "reject")
        self.assertIn("invalid_product_sku", out.reasons)

    def test_reject_sku_without_cleaning_intent(self) -> None:
        out = run_intake_gate(
            {
                "description": "rag query only",
                "product_sku": "CLEAN-BASIC",
            }
        )
        self.assertEqual(out.decision, "reject")
        self.assertIn("sku_without_cleaning_intent", out.reasons)

    def test_reject_empty_request(self) -> None:
        out = run_intake_gate({})
        self.assertFalse(out.ok)
        self.assertEqual(out.decision, "reject")

    def test_suggested_pipeline_not_used_as_billing_sku_on_accept(self) -> None:
        out = run_intake_gate(_accept_basic_payload())
        assert out.phase6_5_pre_state is not None
        order_mapping = (out.phase6_5_pre_state.get("order") or {}).get("field_mapping") or {}
        self.assertNotIn("intake.suggested_pipeline", order_mapping)
        self.assertEqual(out.suggested_pipeline, SUGGESTED_PIPELINE_HINT)


if __name__ == "__main__":
    unittest.main()
