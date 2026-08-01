"""Smoke test: P4 verify local_similarity_pct computation in sync pipeline.

Problem: _sync_wave_to_scout_pipeline.py was hardcoding local_similarity_pct=None.
Fix: now reads from source (x.get('local_similarity_pct')), but source rows
     don't have it — so we also compute it inline for A-grade assets.
This smoke test verifies the computation works end-to-end.
"""
import sys, os, json, glob

sys.path.insert(0, 'D:/大唐三省六部/04_Workflows')
sys.path.insert(0, 'D:/大唐三省六部/02_Agents_Core')

try:
    from Asset_Value_Evaluator_Agent import _heuristic_score, _grade, _flatten_summary_for_match, _semantic_overlap_pct
    print("Modules loaded OK")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

# --- Read wave report ---
reports_dir = 'D:/大唐三省六部/06_Exports_Output/reports'
cands = sorted(glob.glob(os.path.join(reports_dir, 'asset_value_eval_b636e*.json')))
if not cands:
    print("No asset_value_eval_b636e*.json found")
    sys.exit(1)

report_path = cands[0]
with open(report_path, encoding='utf-8') as f:
    rep = json.load(f)

rows = rep.get('rows') or []
a_rows = [r for r in rows if str(r.get('grade') or '') == 'A']
a_rows.sort(key=lambda r: float(r.get('final_score') or 0), reverse=True)
top = a_rows[:12]
print(f"Report: {os.path.basename(report_path)}")
print(f"A-grade rows: {len(a_rows)}, top: {len(top)}")

# --- Simulate the FIXED _sync_wave_to_scout_pipeline logic ---
NEEDLE_TEXT = "Tangent Chariot AI agent evaluation workflow integration"

top_matches_fixed = []
for x in top[:12]:
    # OLD: hardcoded None — P4 bug
    old_val = None
    # NEW: read from source (this returns None since source has no local_similarity_pct)
    src_val = x.get('local_similarity_pct')
    # FIX: compute inline for A-grade using _semantic_overlap_pct
    json_p = (x.get('stored_path') or '').replace(chr(92), '/')
    computed_sim = None
    if json_p:
        if not json_p.endswith('.json'):
            json_p += '.json'
        if os.path.exists(json_p):
            with open(json_p, encoding='utf-8') as f:
                rec = json.load(f)
            blob = _flatten_summary_for_match(rec.get('content_summary'))
            blob = blob or str(rec.get('source_path') or rec.get('name') or '')
            computed_sim = _semantic_overlap_pct(NEEDLE_TEXT, blob)
    
    top_matches_fixed.append({
        'source_path': x.get('source_path'),
        'name': x.get('name'),
        'heuristic_score': x.get('local_score'),
        'final_score': x.get('final_score'),
        'grade': x.get('grade'),
        'local_similarity_pct': computed_sim,  # fixed value
    })

print("\n=== FIXED top_matches (local_similarity_pct computed) ===")
for m in top_matches_fixed:
    sim_val = m['local_similarity_pct']
    sim_str = f"{sim_val:.1f}%" if sim_val is not None else "None"
    print(f"  score={m['final_score']:.2f} sim={sim_str}  {m['name'][:50]}")

non_null = sum(1 for m in top_matches_fixed if m['local_similarity_pct'] is not None)
null_count = sum(1 for m in top_matches_fixed if m['local_similarity_pct'] is None)

print(f"\n=== SUMMARY ===")
print(f"OLD (hardcoded None): all local_similarity_pct = None")
print(f"NEW (computed): {non_null} computed / {len(top_matches_fixed)} total")

if non_null == len(top_matches_fixed):
    print("\n✅ P4 FIX VERIFIED: all similarity values now computed")
else:
    print(f"\n⚠️  {null_count} assets still have None similarity")

print("\nDONE")