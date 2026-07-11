"""Unit tests for Wave 8 M2 sampling design (deterministic SamplingPlan)."""

from __future__ import annotations

import unittest

from core.wave8_m2_sampling_design import (
    W6_BILLING_TABLE_VERSION_DEFAULT,
    build_sampling_plan,
    compute_sample_size,
    derive_seed,
)


class TestComputeSampleSize(unittest.TestCase):
    def test_n_zero(self) -> None:
        self.assertEqual(compute_sample_size(0), 0)

    def test_n_below_20_full_sample(self) -> None:
        for n in (1, 19):
            self.assertEqual(compute_sample_size(n), n)

    def test_n_100_typical(self) -> None:
        self.assertEqual(compute_sample_size(100), 20)


class TestBuildSamplingPlan(unittest.TestCase):
    def test_n_zero_empty_plan(self) -> None:
        plan = build_sampling_plan(0)
        self.assertEqual(plan.N, 0)
        self.assertEqual(plan.sample_size, 0)
        self.assertEqual(plan.row_indexes, ())
        self.assertEqual(plan.stride, None)

    def test_n_one_full_sample(self) -> None:
        plan = build_sampling_plan(1)
        self.assertEqual(plan.sample_size, 1)
        self.assertEqual(plan.row_indexes, (0,))

    def test_n_below_20_full_sample(self) -> None:
        plan = build_sampling_plan(15)
        self.assertEqual(plan.sample_size, 15)
        self.assertEqual(len(plan.row_indexes), 15)
        self.assertEqual(set(plan.row_indexes), set(range(15)))

    def test_n_100_sample_size_and_seed_stable(self) -> None:
        plan_a = build_sampling_plan(100)
        plan_b = build_sampling_plan(100)
        self.assertEqual(plan_a.sample_size, 20)
        self.assertEqual(plan_b.sample_size, 20)
        self.assertEqual(plan_a.seed, plan_b.seed)
        self.assertEqual(
            plan_a.seed,
            derive_seed(billing_table_version=W6_BILLING_TABLE_VERSION_DEFAULT, n=100),
        )
        self.assertEqual(len(plan_a.row_indexes), 20)
        self.assertEqual(len(set(plan_a.row_indexes)), 20)
        self.assertTrue(all(0 <= i < 100 for i in plan_a.row_indexes))

    def test_deterministic_repeated_calls(self) -> None:
        kwargs = {
            "per_extension_counts": {".py": 300, ".md": 250, ".txt": 51},
            "billing_table_version": "w6_billing_v0.1",
        }
        first = build_sampling_plan(601, **kwargs)
        second = build_sampling_plan(601, **kwargs)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_n_gt_500_strata_at_least_one_per_extension(self) -> None:
        counts = {".py": 200, ".js": 150, ".md": 120, ".txt": 80, ".csv": 51}
        n = sum(counts.values())
        self.assertGreater(n, 500)
        plan = build_sampling_plan(n, per_extension_counts=counts)
        self.assertGreaterEqual(plan.sample_size, len(counts))
        for ext in counts:
            self.assertGreaterEqual(plan.strata_coverage.get(ext, 0), 1)

    def test_invariants_sample_size_bounds(self) -> None:
        for n in (0, 1, 19, 100, 501, 1000):
            plan = build_sampling_plan(n)
            self.assertGreaterEqual(plan.sample_size, 0)
            self.assertLessEqual(plan.sample_size, n)
            self.assertEqual(len(plan.row_indexes), plan.sample_size)
            self.assertEqual(len(set(plan.row_indexes)), plan.sample_size)

    def test_per_extension_counts_mismatch_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            build_sampling_plan(
                100,
                per_extension_counts={".py": 50, ".md": 40},
            )
        self.assertIn("must equal N=100", str(ctx.exception))

    def test_negative_count_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_sampling_plan(10, per_extension_counts={".py": -1})

    def test_billing_version_affects_seed(self) -> None:
        a = build_sampling_plan(100, billing_table_version="w6_billing_v0.1")
        b = build_sampling_plan(100, billing_table_version="w6_billing_v0.2")
        self.assertNotEqual(a.seed, b.seed)


if __name__ == "__main__":
    unittest.main()
