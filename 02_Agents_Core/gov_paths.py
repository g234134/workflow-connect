# gov_paths.py — 路徑動態化 + 吏部 .env 載入（配置歸心）
# 所有 Agent 應透過本模組取得六部根目錄與各部門絕對路徑；禁止寫死磁碟路徑。

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Dict, Optional

_ROOT_CACHE: Optional[str] = None


def _load_dotenv(env_path: str) -> None:
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except OSError:
        pass


def _discover_tang_root_from_filesystem() -> str:
    """自本檔所在 02_Agents_Core 向上尋找 04_Workflows/Master_Map.json。"""
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    for _ in range(12):
        candidate = os.path.join(cur, "04_Workflows", "Master_Map.json")
        if os.path.isfile(candidate):
            return os.path.abspath(cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.abspath(os.path.join(here, ".."))


def _read_master_map_at(root: str) -> Dict[str, Any]:
    p = os.path.join(root, "04_Workflows", "Master_Map.json")
    if not os.path.isfile(p):
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def invalidate_caches() -> None:
    global _ROOT_CACHE
    _ROOT_CACHE = None
    load_master_map.cache_clear()


def get_tang_gov_root() -> str:
    """
    六部根目錄。優先順序：
      1) 環境變數 TANG_GOV_ROOT（載入 .env 前後皆會再讀）
      2) 目錄結構推導（找到 04_Workflows/Master_Map.json）
      3) 載入 01_Environments/.env
      4) Master_Map.json 的 tang_gov_root（若非空）
    """
    global _ROOT_CACHE
    if _ROOT_CACHE is not None:
        return _ROOT_CACHE

    root = os.environ.get("TANG_GOV_ROOT", "").strip()
    if not root:
        root = _discover_tang_root_from_filesystem()
    root = os.path.abspath(root)

    env_file = os.path.join(root, "01_Environments", ".env")
    _load_dotenv(env_file)

    env_root = os.environ.get("TANG_GOV_ROOT", "").strip()
    if env_root:
        root = os.path.abspath(env_root)

    data = _read_master_map_at(root)
    tg = str(data.get("tang_gov_root", "")).strip()
    if tg:
        root = os.path.abspath(tg)

    _ROOT_CACHE = root
    return root


@lru_cache(maxsize=1)
def load_master_map() -> Dict[str, Any]:
    root = get_tang_gov_root()
    p = os.path.join(root, "04_Workflows", "Master_Map.json")
    if not os.path.isfile(p):
        raise FileNotFoundError(f"Master_Map.json not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _department_rel(m: Dict[str, Any], key: str) -> str:
    dept = m.get("departments") or m.get("paths") or {}
    aliases = m.get("aliases") or {}
    resolved = aliases.get(key, key)
    rel = dept.get(resolved) or dept.get(key)
    if not rel:
        raise KeyError(f"Master_Map 未定義部門或別名: {key} (resolved={resolved})")
    return rel.replace("/", os.sep)


def _get_subdir_segment_from_map(m: Dict[str, Any], department_key: str, sub_type: str) -> str:
    """由 Master_Map.sub_directories 解析部門下子目錄實際資料夾名稱（sub_type 為邏輯鍵）。"""
    dept_rel = _department_rel(m, department_key)
    bucket = (m.get("sub_directories") or {}).get(dept_rel)
    if not isinstance(bucket, dict):
        raise KeyError(f"Master_Map.sub_directories 未定義或非物件: {dept_rel!r}")
    seg = bucket.get(sub_type)
    if seg is None:
        raise KeyError(f"Master_Map.sub_directories[{dept_rel!r}] 未定義子類型: {sub_type!r}")
    return str(seg).replace("/", os.sep)


def resolve_agent_output_path(
    dest_root: Optional[str],
    department: str,
    sub_type: Optional[str] = None,
) -> str:
    """
    Agent 產出路徑的單一解析入口（部門 + 邏輯 sub_type）。
    dest_root 為 None 時使用 get_tang_gov_root() 與已快取的 Master_Map。
    sub_type 為 None 時回傳部門根目錄（不含 sub_directories 子路徑）。
    """
    if sub_type is None or str(sub_type).strip() == "":
        if dest_root:
            return get_department_under(dest_root, department)
        return get_department(department)

    st = str(sub_type).strip()
    if dest_root:
        root = os.path.abspath(dest_root)
        base = get_department_under(root, department)
        mp = os.path.join(root, "04_Workflows", "Master_Map.json")
        if not os.path.isfile(mp):
            raise FileNotFoundError(mp)
        with open(mp, "r", encoding="utf-8") as f:
            m: Dict[str, Any] = json.load(f)
        sub_seg = _get_subdir_segment_from_map(m, department, st)
        return os.path.normpath(os.path.join(base, sub_seg))

    m = load_master_map()
    base = get_department(department)
    sub_seg = _get_subdir_segment_from_map(m, department, st)
    return os.path.normpath(os.path.join(base, sub_seg))


def get_department(key: str) -> str:
    """回傳部門絕對路徑。key 可為 01_Environments 或 aliases（如 temp_cache）。"""
    m = load_master_map()
    rel = _department_rel(m, key)
    return os.path.normpath(os.path.join(get_tang_gov_root(), rel))


def get_department_under(dest_root: str, key: str) -> str:
    """在指定六部根目錄下解析部門路徑（與全域緩存根無關）。"""
    root = os.path.abspath(dest_root)
    mp = os.path.join(root, "04_Workflows", "Master_Map.json")
    if not os.path.isfile(mp):
        raise FileNotFoundError(mp)
    with open(mp, "r", encoding="utf-8") as f:
        m = json.load(f)
    rel = _department_rel(m, key)
    return os.path.normpath(os.path.join(root, rel))


def get_artifact_rel_path(artifact_key: str) -> str:
    m = load_master_map()
    arts = m.get("artifacts") or {}
    rel = arts.get(artifact_key)
    if not rel:
        raise KeyError(f"Master_Map.artifacts 未定義: {artifact_key}")
    return rel.replace("/", os.sep)


def get_artifact_path(artifact_key: str) -> str:
    rel = get_artifact_rel_path(artifact_key)
    return os.path.normpath(os.path.join(get_tang_gov_root(), rel))


def resolve_artifact_under_root(dest_root: str, artifact_key: str) -> str:
    """在指定根目錄下依 Master_Map.json 的 artifacts 解析路徑（不依賴全域緩存根）。"""
    root = os.path.abspath(dest_root)
    mp = os.path.join(root, "04_Workflows", "Master_Map.json")
    if not os.path.isfile(mp):
        raise FileNotFoundError(mp)
    with open(mp, "r", encoding="utf-8") as f:
        m = json.load(f)
    arts = m.get("artifacts") or {}
    rel = arts.get(artifact_key)
    if not rel:
        raise KeyError(artifact_key)
    return os.path.normpath(os.path.join(root, rel.replace("/", os.sep)))


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """讀取密鑰／設定：保證已載入 .env 後再讀 os.environ。"""
    get_tang_gov_root()
    return os.environ.get(name, default)


def get_agency_agents_root(dest_root: Optional[str] = None) -> str:
    """agency-agents 倉庫根目錄（Master_Map.sub_directories[02_Agents_Core].agency_agents）。"""
    return resolve_agent_output_path(dest_root, "02_Agents_Core", "agency_agents")


def get_crawl4ai_home(dest_root: Optional[str] = None) -> str:
    """
    Crawl4AI 模型／快取目錄。
    優先環境變數 CRAWL4AI_HOME；未設定則使用 05_Temp_Cache/crawl4ai_home。
    """
    get_tang_gov_root()
    raw = os.environ.get("CRAWL4AI_HOME", "").strip()
    if raw:
        home = os.path.abspath(os.path.expanduser(os.path.expandvars(raw)))
    else:
        home = resolve_agent_output_path(dest_root, "05_Temp_Cache", "crawl4ai_home")
    os.makedirs(home, exist_ok=True)
    return home
