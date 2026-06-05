import json
import os
import sys

fp = r"D:\大唐三省六部\06_Exports_Output\reports\asset_value_eval_25c67a4d7c1b4d3eac5dbb59fcc9fe0a.json"
d = json.load(open(fp, "r", encoding="utf-8"))
rows = d["rows"]
a = [r for r in rows if r["grade"] == "A"]
print(f"Total A-grade: {len(a)}")
print(f"Pool / Sampled / Avg: {d['pool_size']} / {d['sampled']} / {d['avg_score']}")
print(f"Grades: {d['grades']}  Groq: {d['groq_calls']}/{d['groq_success']}\n")
for r in a:
    name = r.get("name") or os.path.basename(str(r.get("source_path") or ""))
    used = "Y" if r.get("groq_used") else "N"
    print(f"  {r['final_score']:.2f}  conf={r['confidence']:.2f}  {str(r['original_type']):<14s}  groq={used}  {name}")
