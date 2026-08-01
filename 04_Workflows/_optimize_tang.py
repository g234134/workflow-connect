"""optimize_tang.py — 數據分析優化，正確處理 Windows 路徑"""
import json, os, sys, time, re
from typing import Dict, List, Any
from collections import Counter

TANG_ROOT = "D:/大唐三省六部"
REPORTS_DIR = TANG_ROOT + "/06_Exports_Output/reports"

# 直接精確指定 windows 風格的檔案路徑
EVAL_PATH = TANG_ROOT + "/06_Exports_Output/reports/asset_value_eval_cd2eeb21c8d64b899cb156a9493d2e33.json"
ELITE_PATH = TANG_ROOT + "/06_Exports_Output/reports/elite_cache.json"
RULES_PATH = TANG_ROOT + "/06_Exports_Output/reports/local_judge_rules.json"
OUT_PATH = TANG_ROOT + "/06_Exports_Output/reports/optimization_plan.json"

ELITE_THRESHOLD = 7.5

def progress(i, n, label=""):
    pct = i / n * 100
    bar_len = 30
    filled = int(pct / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    if i >= n:
        print(f"\r  {label} {bar} {i}/{n} ({pct:.1f}%)", flush=True)
        print()
    else:
        print(f"\r  {label} {bar} {i}/{n} ({pct:.1f}%)", end="", flush=True)

print("=== 1. 載入 eval report ===")
print(f"   EVAL_PATH = {EVAL_PATH}")
print(f"   存在? {os.path.exists(EVAL_PATH)}")
t0 = time.time()

with open(EVAL_PATH, "rb") as f:
    raw_bytes = f.read()
print(f"   檔案大小: {len(raw_bytes) / 1024 / 1024:.1f} MB")

# 找 "rows": [ 的開頭
idx = raw_bytes.find(b'"rows":[')
if idx == -1:
    # 可能有空格
    m = re.search(rb'"rows"\s*:\s*\[', raw_bytes)
    if m:
        idx = m.start()
    else:
        idx = raw_bytes.find(b'"rows"')

if idx == -1:
    print("ERROR: rows key not found")
    sys.exit(1)

# find opening bracket
open_br = raw_bytes.find(b'[', idx)
depth = 0
in_str = False
esc = False
close_br = -1
for i in range(open_br, len(raw_bytes)):
    c = raw_bytes[i]
    if esc:
        esc = False
        continue
    if c == 92:  # \
        esc = True
        if in_str:
            continue
    if c == 34:  # "
        in_str = not in_str
        continue
    if in_str:
        continue
    if c == 91:  # [
        depth += 1
    elif c == 93:  # ]
        depth -= 1
        if depth == 0:
            close_br = i
            break

rows_str = raw_bytes[open_br:close_br+1]
print(f"   rows bytes: {len(rows_str) / 1024 / 1024:.2f} MB")

rows = json.loads(rows_str)
print(f"   rows loaded: {len(rows)} in {time.time()-t0:.1f}s")

# ─── 2. 資料分析 ───
print("\n=== 2. 分數分布分析 ===")
total = len(rows)
grades = [r.get("grade") for r in rows]
final_scores = [r.get("final_score") or 0 for r in rows]
local_scores = [r.get("local_score") or 0 for r in rows]

gc = Counter(grades)
print(f"   Grade: A={gc.get('A',0)} ({gc.get('A',0)/total*100:.1f}%)  B={gc.get('B',0)} ({gc.get('B',0)/total*100:.1f}%)  C={gc.get('C',0)} ({gc.get('C',0)/total*100:.1f}%)  D={gc.get('D',0)} ({gc.get('D',0)/total*100:.1f}%)")

# final_score bins 0-10
bins = {s:0 for s in range(0,11)}
for s in final_scores:
    k = max(0, min(10, int(s)))
    bins[k] += 1
print("\n   final_score 分布:")
for s in range(0, 11):
    cnt = bins[s]
    bar = "█" * (cnt // 200 + 1) if cnt else ""
    print(f"     {s}: {cnt:5d} ({cnt/total*100:.1f}%) {bar}")

# elites
sort_finals = sorted(final_scores, reverse=True)
elites = sum(1 for s in final_scores if s > ELITE_THRESHOLD)
print(f"\n   final_score > {ELITE_THRESHOLD} (A級精英): {elites}")
print(f"   top 10 final_scores: {sort_finals[:10]}")
print(f"   p95 final_score: {sort_finals[int(total*0.95)]}")
print(f"   p99 final_score: {sort_finals[int(total*0.99)]}")

# Groq used 誰
groq_used = sum(1 for r in rows if r.get("groq_used"))
groq_success = sum(1 for r in rows if r.get("groq_used") and r.get("groq_value") is not None)
print(f"\n   Groq 使用: {groq_used} 件, 成功: {groq_success}")

# dodge analysis
print("\n=== 3. Dodge 規則分析 ===")
dodgeable = 0
current_dodgeable = 0
for r in rows:
    ls = r.get("local_score") or 0
    conf = r.get("confidence") or 0
    otype = (r.get("original_type") or "").lower()
    ext = (r.get("extension") or "").lower()

    # 當前 dodge_2: ext=.py, otype=unknown, score 4-6, conf<=0.65
    if ext == ".py" and otype == "unknown" and 4.0 <= ls <= 6.0 and conf <= 0.65:
        current_dodgeable += 1
    # dodge_3: ext=.json, otype=unknown, ...
    if ext == ".json" and otype == "unknown" and 4.0 <= ls <= 6.0 and conf <= 0.65:
        current_dodgeable += 1

    # 建議放寬: 任何白名單擴展 + 低配置類型 + ambiguous
    if ext in ('.py','.php','.json','.yml','.yaml','.toml') and otype in ('json','yaml','toml','unknown') and 4.0 <= ls <= 6.0 and conf <= 0.65:
        dodgeable += 1

print(f"   當前規則能匹配: {current_dodgeable} 件")
print(f"   放寬規則能匹配: {dodgeable} 件 (少了 {len(rows) - dodgeable} 件 Groq 呼叫或留空)")
# 這dodgeable件中，多少正在用Groq
dodgeable_with_groq = sum(1 for r in rows if 
    (r.get("extension") or "").lower() in ('.py','.php','.json','.yml','.yaml','.toml') and
    (r.get("original_type") or "").lower() in ('json','yaml','toml','unknown') and
    4.0 <= (r.get("local_score") or 0) <= 6.0 and
    (r.get("confidence") or 0) <= 0.65 and
    r.get("groq_used") is True)
print(f"   其中現正送 Groq 的: {dodgeable_with_groq} 件 (可能可省)")

# Groq failure on dodged-candidates
failed_groq = sum(1 for r in rows if 
    (r.get("extension") or "").lower() in ('.py','.php','.json','.yml','.yaml','.toml') and
    r.get("groq_used") is True and r.get("groq_value") is None)
print(f"   Groq 失敗: {failed_groq} 件（這些送雲端但沒回值）")

# ─── 4. 儲存優化計劃 ───
print("\n=== 4. 寫入優化計畫與方案 ===")

plan = {
    "run_id": "cd2eeb21c8d64b899cb156a9493d2e33",
    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "pool_size": total,
    "grades": dict(gc),
    "avg_final_score": round(sum(final_scores)/total, 3),
    "elite_threshold": ELITE_THRESHOLD,
    "elite_count_by_final": elites,
    "dodge_current_matches": current_dodgeable,
    "dodge_broadened_matches": dodgeable,
    "dodge_sending_groq_now": dodgeable_with_groq,
    "groq_failures": failed_groq,
    "elite_sample": []
}

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(plan, f, indent=2, ensure_ascii=False)

print(f"\n   輸出: {OUT_PATH}")
print("\n========= 分析完成 =========")
print(f"總件數: {total}")
print(f"final_score > 7.5 精英: {elites}")
print(f"Dodge 規則低估: 當前匹配 {current_dodgeable} 件, 放寬後可達 {dodgeable} 件")
print(f"Groq 失敗 {failed_groq} 件——這些送雲端但沒得到有效回應")
