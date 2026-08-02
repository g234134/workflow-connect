#!/usr/bin/env bash
# repo_hygiene_check.sh — 版控衛生檢查（dev-workflow §7 落地執行版）
#
# 用法:
#   bash scripts/repo_hygiene_check.sh            # 檢查目前目錄
#   bash scripts/repo_hygiene_check.sh /path/to/repo  # 檢查指定 repo
#
# 退出碼:
#   0 = 全部通過，可 commit/push
#   1 = 至少一項失敗，先清理再 push（輸出會指出哪一項 + 處置）
#
# 對應 dev-workflow/04_github-rules.md §7 的三條檢查:
#   ① 快取/暫存目錄（05_Temp_Cache/、__pycache__/、.cache/）不在 index
#   ② >50MB 大檔案不在 index
#   ③ 內嵌 git repo（.git 存在且無 .gitmodules 對應）不被追蹤

set -u

REPO_DIR="${1:-$(pwd)}"
cd "$REPO_DIR" 2>/dev/null || { echo "❌ [FAIL] 無法進入目錄: $REPO_DIR"; exit 1; }

# 確認是 git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ [FAIL] 不是 git repo: $REPO_DIR"
  exit 1
fi

FAIL_COUNT=0

echo "🔍 版控衛生檢查: $(git rev-parse --show-toplevel 2>/dev/null || echo "$REPO_DIR")"
echo ""

# ── ① 快取/暫存目錄不得在 index ──────────────────────────────
echo "── ① 快取/暫存目錄檢查 ──"
CACHE_HITS=$(git ls-files | grep -E '(^|/)(05_Temp_Cache|__pycache__|\.cache)(/|$)' || true)
if [ -n "$CACHE_HITS" ]; then
  echo "❌ [FAIL ①] 快取/暫存目錄出現在 index（$(echo "$CACHE_HITS" | wc -l | tr -d ' ') 個）:"
  echo "$CACHE_HITS" | head -20 | sed 's/^/    /'
  echo ""
  echo "    處置: git rm -r --cached <路徑> 後把該目錄加入 .gitignore（工作樹檔案會保留）"
  echo "    驗證: 重跑本腳本直到 ① 顯示 ✅"
  FAIL_COUNT=$((FAIL_COUNT + 1))
else
  echo "✅ [PASS ①] 快取/暫存目錄未進 index"
fi
echo ""

# ── ② >50MB 大檔案不得在 index ───────────────────────────────
echo "── ② 大檔案檢查（>50MB）──"
LARGE_FILES=$(git ls-tree -r -l HEAD 2>/dev/null | awk '$4 > 50000000 {print $5}')
if [ -n "$LARGE_FILES" ]; then
  echo "❌ [FAIL ②] 有 >50MB 的檔案在 index（$(echo "$LARGE_FILES" | wc -l | tr -d ' ') 個）:"
  echo "$LARGE_FILES" | head -20 | sed 's/^/    /'
  echo ""
  echo "    處置: git rm --cached <檔案>（或改用 Git LFS），並把該檔案/目錄加入 .gitignore"
  echo "    驗證: 重跑本腳本直到 ② 顯示 ✅"
  FAIL_COUNT=$((FAIL_COUNT + 1))
else
  echo "✅ [PASS ②] 無 >50MB 大檔案"
fi
echo ""

# ── ③ 內嵌 git repo 不得被追蹤 ───────────────────────────────
echo "── ③ 內嵌 git repo 檢查 ──"
# 3a: index 中的 gitlink（mode 160000）＝內嵌 repo 被當 submodule 追蹤
GITLINKS=$(git ls-files -s | awk '$1 == "160000" {print $4}')
# 3b: index 中出現 .git 內容路徑（.git 被強制追蹤）
GITDIR_HITS=$(git ls-files | grep '/\.git\(/\|$\)' || true)

if [ -n "$GITLINKS" ] || [ -n "$GITDIR_HITS" ]; then
  echo "❌ [FAIL ③] 內嵌 git repo 出現在 index:"
  if [ -n "$GITLINKS" ]; then
    echo "    gitlink（被當 submodule 追蹤）:"
    echo "$GITLINKS" | head -20 | sed 's/^/        /'
  fi
  if [ -n "$GITDIR_HITS" ]; then
    echo "    .git 目錄內容（被強制追蹤）:"
    echo "$GITDIR_HITS" | head -20 | sed 's/^/        /'
  fi
  echo ""
  echo "    處置: git rm --cached <路徑>，把該目錄加入 .gitignore"
  echo "          （若確要共用，改用正式 submodule: git submodule add <url> <路徑>）"
  echo "    驗證: 重跑本腳本直到 ③ 顯示 ✅"
  FAIL_COUNT=$((FAIL_COUNT + 1))
else
  echo "✅ [PASS ③] 無內嵌 git repo 被追蹤"
fi
echo ""

# ── 總結 ──────────────────────────────────────────────────────
if [ "$FAIL_COUNT" -eq 0 ]; then
  echo "🎉 版控衛生檢查全部通過 — 可以 commit / push"
  exit 0
else
  echo "🚫 版控衛生檢查失敗: $FAIL_COUNT 類問題，請依上方處置清理後再 push"
  exit 1
fi
