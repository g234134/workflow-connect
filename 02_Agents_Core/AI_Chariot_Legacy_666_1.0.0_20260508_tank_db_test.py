import os
import sqlite3
import csv
import re
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:8000/v1"
os.environ["OPENAI_API_KEY"] = "sk-tank-31"

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
_CSV_SAME_DIR = _HERE / "dirty_data_100k.csv"
_CSV_IN_HARNESS_DATA = _HERE / "data" / "dirty_data_100k.csv"
_CSV_REPO_DATA = _REPO_ROOT / "data" / "dirty_data_100k.csv"


def _pick_csv_path() -> Path:
    if _CSV_SAME_DIR.exists():
        return _CSV_SAME_DIR
    if _CSV_IN_HARNESS_DATA.exists():
        return _CSV_IN_HARNESS_DATA
    if _CSV_REPO_DATA.exists():
        return _CSV_REPO_DATA
    raise FileNotFoundError(
        "找不到 dirty_data_100k.csv。請放在 harness/、harness/data/，或 repo 的 data/dirty_data_100k.csv。"
    )


_RE_HTML = re.compile(r"<[^>]+>")
_RE_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_RE_MULTI_SPACE = re.compile(r"\s+")


def _clean_text(s: object) -> str:
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\ufeff", "")  # BOM
    s = s.replace("\uFFFD", "")  # replacement char "�"
    s = _RE_HTML.sub("", s)
    s = _RE_CTRL.sub("", s)
    s = s.strip()
    for bad in ("undefined", "NaN", "---廣告贊助---", "點我領取優惠"):
        s = s.replace(bad, "")
    s = _RE_MULTI_SPACE.sub(" ", s).strip()
    s = s.lstrip("!@#$%^&*()_+=-~`|\\/?.,:;[]{}<>")
    return s.strip()


def _clean_category(s: object) -> str:
    s = _clean_text(s).lower()
    if not s:
        return ""
    if s in {"電器", "家電"}:
        return "electronics"
    if "electro" in s:
        return "electronics"
    if "gadget" in s:
        return "gadgets"
    return s


def _parse_date(s: object) -> str:
    s = _clean_text(s)
    if not s:
        return ""
    try:
        return datetime.strptime(s, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return s


def _ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cleaned_products (
          row_id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_id INTEGER,
          product_name_clean TEXT,
          price INTEGER,
          date TEXT,
          category_clean TEXT,
          raw_product_name TEXT,
          raw_category TEXT,
          inserted_at TEXT
        )
        """
    )
    # 來源檔的 id 對應 source_id，避免重複匯入造成資料暴增
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_cleaned_products_source_id
        ON cleaned_products(source_id)
        WHERE source_id IS NOT NULL
        """
    )
    conn.commit()


def _fetch_db_stats(conn: sqlite3.Connection) -> dict[str, int]:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cleaned_products")
    total = int(cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM cleaned_products WHERE source_id IS NULL")
    null_source_id = int(cur.fetchone()[0])
    return {"total_rows": total, "null_source_id_rows": null_source_id}


def _format_table(rows: list[tuple[str, str]], title: str = "執行結果") -> str:
    # 若有 rich，就用更漂亮的表格；否則 fallback 純文字表格
    try:
        from rich.console import Console  # type: ignore
        from rich.table import Table  # type: ignore

        table = Table(title=title, show_lines=False, header_style="bold")
        table.add_column("項目", style="bold cyan", no_wrap=True)
        table.add_column("值", style="white")
        for k, v in rows:
            table.add_row(k, v)
        Console().print(table)
        return ""
    except Exception:
        pass

    col1 = max(len(k) for k, _ in rows) if rows else 2
    col2 = max(len(v) for _, v in rows) if rows else 2
    line = f"+-{'-' * col1}-+-{'-' * col2}-+"
    out = [f"\n{title}", line]
    out.append(f"| {'項目'.ljust(col1)} | {'值'.ljust(col2)} |")
    out.append(line)
    for k, v in rows:
        out.append(f"| {k.ljust(col1)} | {v.ljust(col2)} |")
    out.append(line)
    return "\n".join(out)


def _notify(title: str, message: str) -> None:
    # Windows：用 MessageBox，不需要額外套件
    try:
        import ctypes

        MB_OK = 0x0
        ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK)
    except Exception:
        pass


class ProcessDirtyCsvTool(BaseTool):
    name: str = "process_dirty_csv"
    description: str = (
        "讀取 dirty_data_100k.csv（同目錄優先；否則讀 data/dirty_data_100k.csv），"
        "每次抓 batch_size 筆（預設 5），清洗後寫入 tank_data.db 的 cleaned_products。"
        "參數：batch_size（整數）、max_batches（整數或留空）。"
    )

    def _run(
        self,
        batch_size: int = 5,
        max_batches: int | str | None = None,
        reset_table: bool = False,
    ) -> str:
        if batch_size <= 0:
            raise ValueError("batch_size 必須 > 0")
        if isinstance(max_batches, str):
            max_batches = max_batches.strip()
            max_batches = int(max_batches) if max_batches else None
        if max_batches is not None and int(max_batches) <= 0:
            raise ValueError("max_batches 若有值，必須 > 0")
        max_batches = int(max_batches) if max_batches is not None else None

        csv_path = _pick_csv_path()
        conn = sqlite3.connect("tank_data.db")
        try:
            _ensure_schema(conn)
            before = _fetch_db_stats(conn)
            if reset_table:
                conn.execute("DELETE FROM cleaned_products")
                conn.commit()
                before = _fetch_db_stats(conn)
            inserted = 0
            batches = 0
            t0 = time.perf_counter()

            with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.DictReader(f)
                batch: list[dict[str, str]] = []

                def flush(rows: list[dict[str, str]]) -> int:
                    cur = conn.cursor()
                    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
                    for r in rows:
                        raw_name = r.get("product_name", "")
                        raw_cat = r.get("category", "")

                        name_clean = _clean_text(raw_name)
                        cat_clean = _clean_category(raw_cat)
                        date_norm = _parse_date(r.get("date", ""))

                        try:
                            source_id = int(_clean_text(r.get("id", "")))
                        except ValueError:
                            source_id = None

                        price_raw = _clean_text(r.get("price", ""))
                        try:
                            price = int(price_raw) if price_raw else None
                        except ValueError:
                            price = None

                        cur.execute(
                            """
                            INSERT OR REPLACE INTO cleaned_products
                              (source_id, product_name_clean, price, date, category_clean, raw_product_name, raw_category, inserted_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                source_id,
                                name_clean,
                                price,
                                date_norm,
                                cat_clean,
                                str(raw_name),
                                str(raw_cat),
                                now,
                            ),
                        )
                    conn.commit()
                    return len(rows)

                for row in reader:
                    batch.append(row)
                    if len(batch) >= batch_size:
                        inserted += flush(batch)
                        batches += 1
                        batch = []
                        if max_batches is not None and batches >= max_batches:
                            break

                if batch and (max_batches is None or batches < max_batches):
                    inserted += flush(batch)
                    batches += 1

            elapsed_s = time.perf_counter() - t0
            after = _fetch_db_stats(conn)
            delta_rows = after["total_rows"] - before["total_rows"]
            return (
                "OK"
                f" batches={batches}"
                f" batch_size={batch_size}"
                f" processed_rows={inserted}"
                f" delta_rows={delta_rows}"
                f" elapsed_s={elapsed_s:.2f}"
                f" csv={csv_path}"
                " db=tank_data.db"
            )
        finally:
            conn.close()


db_tool = ProcessDirtyCsvTool()

db_admin = Agent(
    role="戰車資料官",
    goal="必須使用工具清洗並寫入資料庫，不准只用口頭回報",
    backstory=(
        "你是一個行動派的資料管理員。你深知「說到做到」的重要性，"
        "若不呼叫 process_dirty_csv 工具，你的任務就是失敗。"
    ),
    llm="ollama/llama3.1",
    tools=[db_tool],
    verbose=True,
    max_iter=3,
)

db_task = Task(
    description=(
        "請讀取 dirty_data_100k.csv（同目錄優先；否則讀 data/dirty_data_100k.csv）。\n"
        "需求：每次只抓 5 筆資料（batch_size=5），清洗掉常見亂碼/髒字串/HTML 後，存入 SQLite（tank_data.db）。\n"
        "你必須呼叫一次 process_dirty_csv 工具，且參數 batch_size=5。\n"
        "你也可以選擇是否傳 max_batches；不傳代表全部，傳 1 代表先示範一批。"
    ),
    expected_output="確認工具回傳成功後的繁體中文完成回報（不要輸出 JSON）。",
    agent=db_admin,
)

def _print_summary(title: str, csv_path_str: str, extra_rows: list[tuple[str, str]] | None = None) -> None:
    try:
        conn = sqlite3.connect("tank_data.db")
        stats = _fetch_db_stats(conn)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    summary_rows = [
        ("CSV", csv_path_str),
        ("DB", str((_HERE / "tank_data.db").resolve())),
        ("Table", "cleaned_products"),
        ("Total rows", str(stats.get("total_rows", 0))),
        ("source_id is NULL", str(stats.get("null_source_id_rows", 0))),
    ]
    if extra_rows:
        summary_rows.extend(extra_rows)

    fallback_table = _format_table(summary_rows, title=title)
    if fallback_table:
        print(fallback_table)

    _notify(
        "資料清洗入庫完成",
        f"已完成。cleaned_products rows={stats.get('total_rows', 0)}\nCSV={csv_path_str}",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="清洗 dirty_data_100k.csv 並寫入 SQLite")
    parser.add_argument("--batch-size", type=int, default=5, help="每批處理筆數（預設 5）")
    parser.add_argument("--max-batches", default=None, help="最多處理幾批（留空代表全部）")
    parser.add_argument("--reset", action="store_true", help="先清空 cleaned_products 再匯入")
    parser.add_argument(
        "--use-agent",
        action="store_true",
        help="改用 CrewAI Agent 來呼叫工具（較慢且可能受 LLM 輸出影響）",
    )
    args = parser.parse_args()

    try:
        csv_path_str = str(_pick_csv_path())
    except Exception:
        csv_path_str = "(unknown)"

    print("\n[資料清洗入庫] 讀 CSV、每次 5 筆、清洗後寫入 SQLite...")

    if args.use_agent:
        # 盡量約束 agent：不要 reset_table、不要 JSON
        db_task.description = (
            "請呼叫一次 process_dirty_csv 工具。\n"
            f"參數：batch_size={args.batch_size}、max_batches={args.max_batches or ''}、reset_table={bool(args.reset)}。\n"
            "重要：Final Answer 請用繁體中文一句話回報，不要輸出 JSON。"
        )
        result = Crew(agents=[db_admin], tasks=[db_task]).kickoff()
        _print_summary(
            "資料清洗入庫 - 執行摘要",
            csv_path_str,
            extra_rows=[("Mode", "agent"), ("Result type", type(result).__name__)],
        )
        return 0

    # 預設：直接執行工具（穩定、可重現），不依賴 LLM 輸出
    tool_result = db_tool._run(
        batch_size=args.batch_size,
        max_batches=args.max_batches,
        reset_table=bool(args.reset),
    )
    _print_summary(
        "資料清洗入庫 - 執行摘要",
        csv_path_str,
        extra_rows=[("Mode", "direct"), ("Tool result", tool_result)],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
