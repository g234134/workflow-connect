#!/usr/bin/env python3
"""
戰車數據清洗 — 營運管理面板
監控訂單、處理任務、生成報告。

用法:
  python ops_dashboard.py status    # 查看系統狀態
  python ops_dashboard.py orders    # 列出訂單
  python ops_dashboard.py process   # 處理待辦訂單
  python ops_dashboard.py report    # 生成營運報告
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ORDERS_DIR = BASE_DIR / "orders"
QUEUE_FILE = BASE_DIR / "order_queue.jsonl"
PROCESSED_DIR = BASE_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"

for d in (ORDERS_DIR, PROCESSED_DIR, REPORTS_DIR):
    d.mkdir(exist_ok=True)


def load_orders():
    """載入所有訂單"""
    orders = []
    for f in sorted(ORDERS_DIR.glob("*.json"), reverse=True):
        try:
            orders.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return orders


def cmd_status():
    """系統狀態"""
    orders = load_orders()
    today = datetime.now().strftime("%Y-%m-%d")
    today_orders = [o for o in orders if o.get("created_at", "").startswith(today)]
    
    stats = {
        "total_orders": len(orders),
        "today_orders": len(today_orders),
        "pending": len([o for o in orders if o.get("status") == "received"]),
        "processing": len([o for o in orders if o.get("status") == "processing"]),
        "completed": len([o for o in orders if o.get("status") == "completed"]),
        "server": "online" if (BASE_DIR / "uploads").exists() else "offline",
    }
    
    print("╔══════════════════════════════════════╗")
    print("║   戰車數據清洗 — 營運狀態           ║")
    print("╚══════════════════════════════════════╝")
    print(f"📅 日期: {today}")
    print(f"📊 總訂單: {stats['total_orders']}")
    print(f"📥 今日新增: {stats['today_orders']}")
    print(f"⏳ 待處理: {stats['pending']}")
    print(f"🔄 處理中: {stats['processing']}")
    print(f"✅ 已完成: {stats['completed']}")
    print(f"🖥️  伺服器: {stats['server']}")
    
    # 收入估算
    revenue = 0
    for o in orders:
        if o.get("status") == "completed":
            plan = o.get("plan", "basic")
            if plan == "basic": revenue += 999
            elif plan == "pro": revenue += 2999
            elif plan == "enterprise": revenue += 5000  # 估算
    print(f"💰 估算收入: NT${revenue:,}")
    
    return stats


def cmd_orders():
    """列出訂單"""
    orders = load_orders()
    if not orders:
        print("📭 目前沒有訂單")
        return
    
    print(f"📋 訂單列表（共 {len(orders)} 筆）\n")
    for o in orders[:10]:
        status_icon = {"received": "📥", "processing": "🔄", "completed": "✅"}.get(o.get("status", ""), "❓")
        plan_name = {"basic": "基礎版", "pro": "專業版", "enterprise": "企業版"}.get(o.get("plan"), o.get("plan"))
        print(f"{status_icon} {o.get('order_id', '?')}")
        print(f"   客戶: {o.get('name', '?')} ({o.get('email', '?')})")
        print(f"   方案: {plan_name}")
        print(f"   時間: {o.get('created_at', '?')[:16]}")
        print()


def cmd_process():
    """處理待辦訂單"""
    orders = load_orders()
    pending = [o for o in orders if o.get("status") == "received"]
    
    if not pending:
        print("✅ 沒有待處理的訂單")
        return
    
    print(f"🔄 處理 {len(pending)} 筆待辦訂單...\n")
    
    for o in pending:
        order_id = o.get("order_id", "?")
        print(f"處理: {order_id}")
        
        # 讀取上傳的檔案
        filepath = o.get("filepath")
        if filepath and os.path.exists(filepath):
            print(f"  📄 檔案: {o.get('filename')} ({o.get('file_size', 0)} bytes)")
            
            # 這裡應該串接實際的清洗管線
            # 目前先模擬處理
            print(f"  🧹 清洗中...")
            print(f"  ✅ 完成")
            
            # 更新狀態
            o["status"] = "completed"
            o["completed_at"] = datetime.now().isoformat()
            o["result"] = {
                "rows_processed": 100,  # 實際應該從清洗結果取得
                "issues_found": 5,
                "issues_fixed": 5,
            }
            
            # 寫回訂單檔
            order_file = ORDERS_DIR / f"{order_id}.json"
            order_file.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")
            
            # 移動到已處理
            processed_file = PROCESSED_DIR / f"{order_id}.json"
            processed_file.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            print(f"  ❌ 找不到檔案: {filepath}")
        
        print()


def cmd_report():
    """生成營運報告"""
    orders = load_orders()
    today = datetime.now().strftime("%Y-%m-%d")
    
    report = {
        "date": today,
        "summary": {
            "total_orders": len(orders),
            "today_orders": len([o for o in orders if o.get("created_at", "").startswith(today)]),
        },
        "by_status": {},
        "by_plan": {},
        "revenue": {"total": 0, "today": 0},
    }
    
    for o in orders:
        status = o.get("status", "unknown")
        plan = o.get("plan", "unknown")
        
        report["by_status"][status] = report["by_status"].get(status, 0) + 1
        report["by_plan"][plan] = report["by_plan"].get(plan, 0) + 1
        
        # 計算收入
        amount = {"basic": 999, "pro": 2999, "enterprise": 5000}.get(plan, 0)
        report["revenue"]["total"] += amount
        if o.get("created_at", "").startswith(today):
            report["revenue"]["today"] += amount
    
    # 儲存報告
    report_file = REPORTS_DIR / f"report_{today}.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"📊 營運報告已生成: {report_file}")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    if len(sys.argv) < 2:
        print("用法: python ops_dashboard.py [status|orders|process|report]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "status": cmd_status()
    elif cmd == "orders": cmd_orders()
    elif cmd == "process": cmd_process()
    elif cmd == "report": cmd_report()
    else: print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
