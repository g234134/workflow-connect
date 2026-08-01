"""Smoke test: P1 7.5 threshold catches real A-grade assets.

Reads from asset_value_eval_b636e*.json (the actual source that _build_elite_index.py uses).
"""
import sys, os, json, glob

sys.path.insert(0, 'D:/大唐三省六部/04_Workflows')
sys.path.insert(0, 'D:/大唐三省六部/02_Agents_Core')

try:
    from Asset_Value_Evaluator_Agent import _heuristic_score, _grade
    print("Modules loaded OK")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

# Read the actual wave report that _build_elite_index.py scans
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
print(f"Wave report: {os.path.basename(report_path)}")
print(f"Found {len(a_rows)} A-grade rows | threshold now=7.5")

elites = []
skipped = []

for r in a_rows:
    stored_path = r.get('stored_path') or ''
    if not stored_path:
        skipped.append("[no-stored_path]")
        continue

    sp = stored_path.replace(chr(92), '/')
    json_p = sp if sp.endswith('.json') else sp + '.json'

    if not os.path.exists(json_p):
        skipped.append(f"[no-file] {os.path.basename(sp)}")
        continue

    with open(json_p, encoding='utf-8') as f:
        rec = json.load(f)

    h, conf, tags = _heuristic_score(rec)
    gr = _grade(h)
    is_elite = h > 7.5 and gr == 'A'
    tag = 'ELITE' if is_elite else 'skip'
    line = f"  [{tag}] score={h:.3f} grade={gr}  {os.path.basename(sp)}"
    if is_elite:
        elites.append(line)
    else:
        skipped.append(line)

print("\n=== ELITE (will enter cache) ===")
for e in elites:
    print(e)
print(f"\nTotal ELITE: {len(elites)} / {len(a_rows)}")

print("\n=== SKIPPED (below 7.5 or not graded A) ===")
for s in skipped:
    print(f"  {s}")
print(f"\nTotal SKIP: {len(skipped)}")

# Summary
print("\n=== SUMMARY ===")
print(f"OLD threshold 9.0: elite_count=0 (all A-grade blocked)")
print(f"NEW threshold 7.5: elite_count={len(elites)} (A-grade now eligible)")
print("\nDONE")