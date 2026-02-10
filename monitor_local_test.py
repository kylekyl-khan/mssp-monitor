"""
CrowdStrike MSSP Monitor - 本機測試版
=====================================
用途：在不需要 Docker / InfluxDB / Prometheus 的情況下，
     直接測試 CrowdStrike API 是否能正常抓到資料。

使用方式：
  1. 安裝依賴：pip install crowdstrike-falconpy python-dotenv
  2. 在同一層目錄放好 .env 檔案
  3. 執行：python monitor_local_test.py

輸出：
  - Terminal 表格報告
  - test_output.json（每次掃描結果）
  - test_history.log（歷史紀錄）
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# ── 嘗試載入 .env（找到就用，找不到也不報錯）──────────────
try:
    from dotenv import load_dotenv
    # 從當前目錄往上找 .env 檔案
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    print(f"[✓] 已載入 .env：{env_path}")
except ImportError:
    print("[!] python-dotenv 未安裝，將直接讀取系統環境變數")
    print("    可執行：pip install python-dotenv")

# ── 嘗試載入 FalconPy ─────────────────────────────────────
try:
    from falconpy import Hosts, FlightControl, OAuth2
    FALCONPY_AVAILABLE = True
except ImportError:
    FALCONPY_AVAILABLE = False
    print("[!] crowdstrike-falconpy 未安裝")
    print("    可執行：pip install crowdstrike-falconpy")


# ═══════════════════════════════════════════════════════════
#  設定區（從 .env 讀取，.env 沒有就用預設值）
# ═══════════════════════════════════════════════════════════
CONFIG = {
    "client_id":          os.getenv("CS_CLIENT_ID"),
    "client_secret":      os.getenv("CS_CLIENT_SECRET"),
    "base_url":           os.getenv("CS_BASE_URL", "us2"),
    "parent_display_name": os.getenv("PARENT_DISPLAY_NAME", "AISHIELD_HQ"),
    "pinned_cids":        [c.strip() for c in os.getenv("PINNED_CIDS", "").split(",") if c.strip()],
    "license_threshold":  int(os.getenv("LICENSE_THRESHOLD", "375")),
    "check_interval":     int(os.getenv("CHECK_INTERVAL", "3600")),
}

# 測試版專用的本機檔案路徑（不用 /data/，直接放在當前目錄）
STATE_FILE  = "test_output.json"
LOG_FILE    = "test_history.log"

# ── 日誌設定（同時寫入檔案和 terminal）──────────────────
logging.basicConfig(
    level=logging.WARNING,          # 只顯示 WARNING 以上，讓 terminal 更乾淨
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  前置檢查
# ═══════════════════════════════════════════════════════════
def preflight_check() -> bool:
    """啟動前檢查所有必要條件"""
    ok = True
    print()
    print("┌─────────────────────────────────────────┐")
    print("│         前置檢查                         │")
    print("└─────────────────────────────────────────┘")

    # 檢查 FalconPy
    if FALCONPY_AVAILABLE:
        print("  [✓] crowdstrike-falconpy 已安裝")
    else:
        print("  [✗] crowdstrike-falconpy 未安裝")
        print("      請執行：pip install crowdstrike-falconpy")
        ok = False

    # 檢查 Client ID
    if CONFIG["client_id"]:
        masked = CONFIG["client_id"][:6] + "..." + CONFIG["client_id"][-4:]
        print(f"  [✓] CS_CLIENT_ID：{masked}")
    else:
        print("  [✗] CS_CLIENT_ID 未設定（請確認 .env 檔案）")
        ok = False

    # 檢查 Client Secret
    if CONFIG["client_secret"]:
        print(f"  [✓] CS_CLIENT_SECRET：{'*' * 16}")
    else:
        print("  [✗] CS_CLIENT_SECRET 未設定（請確認 .env 檔案）")
        ok = False

    # 顯示其他設定
    print(f"  [i] Base URL：{CONFIG['base_url']}")
    print(f"  [i] 授權閾值：{CONFIG['license_threshold']} 台")
    print(f"  [i] Pinned CIDs：{len(CONFIG['pinned_cids'])} 個")
    if CONFIG["pinned_cids"]:
        for cid in CONFIG["pinned_cids"]:
            print(f"        - {cid}")

    print()
    return ok


# ═══════════════════════════════════════════════════════════
#  主要測試邏輯
# ═══════════════════════════════════════════════════════════
class LocalTester:

    def __init__(self):
        self.creds = {
            "client_id":     CONFIG["client_id"],
            "client_secret": CONFIG["client_secret"],
            "base_url":      CONFIG["base_url"],
        }
        self.parent_cid  = "unknown"
        self.pinned_list = [c.lower() for c in CONFIG["pinned_cids"]]

    # ── Step 1：驗證 API 憑證 ─────────────────────────────
    def step1_auth(self) -> bool:
        print("┌─────────────────────────────────────────┐")
        print("│  Step 1 / 4  CrowdStrike API 認證        │")
        print("└─────────────────────────────────────────┘")

        try:
            auth = OAuth2(**self.creds)
            resp = auth.token()
            code = resp["status_code"]

            if code == 201:
                print(f"  [✓] 認證成功（HTTP {code}）")
                # 取得 Parent CID
                temp_hosts = Hosts(**self.creds)
                r = temp_hosts.query_devices_by_filter(limit=1)
                self.parent_cid = r["body"]["meta"]["pagination"].get("cid", "unknown").lower()
                print(f"  [✓] Parent CID：{self.parent_cid}")
                print()
                return True
            else:
                print(f"  [✗] 認證失敗（HTTP {code}）")
                print(f"      錯誤詳情：{resp['body'].get('errors', '未知錯誤')}")
                print()
                print("  常見原因：")
                print("  1. Client ID 或 Secret 填錯")
                print("  2. API 金鑰已過期或被撤銷")
                print("  3. 網路無法連到 CrowdStrike（檢查防火牆/Proxy）")
                print()
                return False

        except Exception as e:
            print(f"  [✗] 連線時發生例外：{e}")
            print()
            return False

    # ── Step 2：取得租戶清單 ──────────────────────────────
    def step2_tenants(self) -> dict:
        print("┌─────────────────────────────────────────┐")
        print("│  Step 2 / 4  取得租戶清單                │")
        print("└─────────────────────────────────────────┘")

        fc         = FlightControl(**self.creds)
        child_cids = set()
        offset     = 0

        print("  正在查詢子租戶 CID 列表...", end="", flush=True)
        try:
            while True:
                resp = fc.query_children(limit=100, offset=offset)
                ids  = resp["body"].get("resources", [])
                for cid in ids:
                    child_cids.add(cid.lower())
                total  = resp["body"].get("meta", {}).get("pagination", {}).get("total", 0)
                offset += len(ids)
                if offset >= total or not ids:
                    break
            print(f" 找到 {len(child_cids)} 個子 CID")
        except Exception as e:
            print(f"\n  [✗] 查詢子 CID 失敗：{e}")
            return {}

        # 批次查詢名稱
        tenant_map = {}
        if child_cids:
            print("  正在查詢租戶名稱...", end="", flush=True)
            try:
                cid_list = list(child_cids)
                for i in range(0, len(cid_list), 100):
                    batch  = cid_list[i:i+100]
                    detail = fc.get_children(ids=batch)
                    for item in detail["body"].get("resources", []):
                        cid  = item["child_cid"].lower()
                        name = item.get("name", cid)
                        tenant_map[cid] = name
                print(f" 取得 {len(tenant_map)} 個名稱")
            except Exception as e:
                print(f"\n  [!] 查詢名稱時發生錯誤：{e}（將用 CID 代替）")

        # 組合結果，加入 Parent
        final_map = {}
        for cid in child_cids:
            final_map[cid] = tenant_map.get(cid, f"[未知名稱] {cid[:8]}...")
        final_map[self.parent_cid] = CONFIG["parent_display_name"]

        # 統計 Pinned 是否都在清單內
        found_pinned    = [c for c in self.pinned_list if c in final_map]
        missing_pinned  = [c for c in self.pinned_list if c not in final_map]

        print(f"\n  [✓] 共 {len(final_map)} 個租戶（含 Parent）")
        print(f"  [✓] Pinned CIDs 找到 {len(found_pinned)} / {len(self.pinned_list)} 個", end="")
        if missing_pinned:
            print(f"\n  [!] 以下 Pinned CID 在租戶清單中找不到：")
            for c in missing_pinned:
                print(f"      - {c}  （請確認 .env 的 PINNED_CIDS 是否填寫正確）")
        else:
            print(" ✓")
        print()
        return final_map

    # ── Step 3：逐一抓取端點數量 ──────────────────────────
    def step3_fetch_counts(self, tenant_map: dict) -> dict:
        print("┌─────────────────────────────────────────┐")
        print("│  Step 3 / 4  抓取各租戶端點數量          │")
        print("└─────────────────────────────────────────┘")

        results = {}
        errors  = []
        total   = len(tenant_map)

        for idx, (cid, name) in enumerate(tenant_map.items(), start=1):
            print(f"  [{idx:>3}/{total}] {name[:35]:<35}", end="", flush=True)
            try:
                is_parent = (cid == self.parent_cid)
                hosts_api = Hosts(**self.creds, member_cid=None if is_parent else cid)
                resp      = hosts_api.query_devices_by_filter_scroll(
                    filter="last_seen:>'now-7d'", limit=1
                )
                if resp["status_code"] == 200:
                    count = resp["body"]["meta"]["pagination"]["total"]
                    print(f"  →  {count:>5} 台")
                    results[cid] = {"name": name, "count": count, "status": "ok"}
                else:
                    code = resp["status_code"]
                    print(f"  →  [!] API 錯誤 {code}")
                    results[cid] = {"name": name, "count": 0, "status": f"api_error_{code}"}
                    errors.append((name, cid, f"API 回傳 {code}"))

            except Exception as e:
                print(f"  →  [!] 例外：{str(e)[:30]}")
                results[cid] = {"name": name, "count": 0, "status": "exception"}
                errors.append((name, cid, str(e)))

        print()
        if errors:
            print(f"  [!] 共 {len(errors)} 個租戶查詢失敗：")
            for name, cid, err in errors:
                print(f"      - {name} ({cid[:8]}...)：{err}")
            print()

        return results

    # ── Step 4：輸出報告 ──────────────────────────────────
    def step4_report(self, results: dict):
        print("┌─────────────────────────────────────────┐")
        print("│  Step 4 / 4  產出報告                    │")
        print("└─────────────────────────────────────────┘")

        fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        threshold  = CONFIG["license_threshold"]

        # 讀取上次結果（用來計算增減）
        old_data = {}
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                print(f"  [✓] 找到上次紀錄（{STATE_FILE}），將計算增減")
            except Exception:
                print(f"  [!] 讀取上次紀錄失敗，Change 欄位將顯示 N/A")
        else:
            print(f"  [i] 找不到上次紀錄，這是第一次執行，Change 欄位全為 0")
        print()

        # ── 分類 ─────────────────────────────────────────
        parent_rows, pinned_rows, other_rows = [], [], []
        pinned_total = 0

        for cid, data in results.items():
            name      = data["name"]
            current   = data["count"]
            old_count = old_data.get(cid, {}).get("count", 0) if isinstance(old_data.get(cid), dict) else old_data.get(cid, 0)
            change    = current - old_count
            is_pinned = cid in self.pinned_list
            status    = data["status"]

            if change > 0:   change_str = f"+{change} ▲"
            elif change < 0: change_str = f"{change} ▼"
            else:            change_str = "  0  -"

            flag = "📌 PINNED" if is_pinned else ("⚠ ERROR" if status != "ok" else "")
            row  = (name, cid, old_count, current, change_str, flag, status)

            if cid == self.parent_cid:
                parent_rows.append(row)
            elif is_pinned:
                pinned_rows.append(row)
                if status == "ok":
                    pinned_total += current
            else:
                other_rows.append(row)

        other_rows.sort(key=lambda x: x[0])

        # ── 表格輸出 ──────────────────────────────────────
        COL = {"name": 32, "cid": 36, "old": 6, "cur": 6, "chg": 8, "flag": 10}
        W   = sum(COL.values()) + len(COL) * 3 + 1

        def row_str(name, cid, old, cur, chg, flag, *_):
            return (
                f"| {str(name):<{COL['name']}} "
                f"| {str(cid):<{COL['cid']}} "
                f"| {str(old):>{COL['old']}} "
                f"| {str(cur):>{COL['cur']}} "
                f"| {str(chg):>{COL['chg']}} "
                f"| {str(flag):<{COL['flag']}} |"
            )

        sep    = "+" + "+".join("-" * (v + 2) for v in COL.values()) + "+"
        header = row_str("Tenant Name", "CID", "Old", "Now", "Change", "Flag")

        print("=" * W)
        print(f"  CrowdStrike MSSP 掃描報告  ── 本機測試版  ──  {fetch_time}")
        print("=" * W)
        print(sep)
        print(header)
        print(sep)

        def print_section(rows, label):
            if not rows:
                return
            print(f"| {label:<{W - 4}} |")
            print(sep)
            for r in rows:
                print(row_str(*r))
            print(sep)

        print_section(parent_rows, "▶ PARENT")
        print_section(pinned_rows, "▶ PINNED CIDs（重點監控）")
        print_section(other_rows,  "▶ Other Tenants")

        # ── Pinned 授權進度條 ─────────────────────────────
        over      = pinned_total > threshold
        filled    = int(min(pinned_total / max(threshold, 1), 1.0) * 30)
        bar       = "█" * filled + "░" * (30 - filled)
        status_ic = "❌ 超過閾值！請確認授權數量" if over else "✅ 正常"

        print(f"  📌 Pinned CIDs 授權加總：")
        print(f"  [{bar}] {pinned_total} / {threshold}  {status_ic}")
        print("=" * W)

        # ── 存檔 ──────────────────────────────────────────
        save_data = {cid: data["count"] for cid, data in results.items()}
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4, ensure_ascii=False)

        # 寫歷史 log
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Scan Time: {fetch_time}\n")
            for cid, data in results.items():
                f.write(f"  {data['name']:<35} {cid}  count={data['count']}  status={data['status']}\n")
            f.write(f"  Pinned Total: {pinned_total} / {threshold}  over={over}\n")

        print()
        print(f"  [✓] 掃描結果已儲存至：{STATE_FILE}")
        print(f"  [✓] 歷史紀錄已寫入：{LOG_FILE}")
        print()

        # ── DB 整合提示 ───────────────────────────────────
        print("  ─────────────────────────────────────────")
        print("  📋 下一步：接上 DB")
        print("  ─────────────────────────────────────────")
        print("  資料確認無誤後，依以下順序整合：")
        print()
        print("  1. 啟動 Docker 服務：")
        print("     docker-compose up -d influxdb prometheus")
        print()
        print("  2. 確認 InfluxDB 就緒：")
        print("     瀏覽器開啟 http://localhost:8086")
        print()
        print("  3. 啟動完整監控系統：")
        print("     docker-compose up -d")
        print()
        print("  4. 觀察 DB 寫入是否正常：")
        print("     docker-compose logs -f mssp-monitor")
        print("  ─────────────────────────────────────────")
        print()

    # ── 執行全部步驟 ──────────────────────────────────────
    def run(self):
        print()
        print("╔══════════════════════════════════════════════════╗")
        print("║  CrowdStrike MSSP Monitor  ── 本機測試模式        ║")
        print("║  不需要 Docker / InfluxDB / Prometheus            ║")
        print("╚══════════════════════════════════════════════════╝")
        print()

        if not self.step1_auth():
            print("  [✗] Step 1 失敗，中止測試")
            return

        tenant_map = self.step2_tenants()
        if not tenant_map:
            print("  [✗] Step 2 失敗，中止測試")
            return

        results = self.step3_fetch_counts(tenant_map)
        if not results:
            print("  [✗] Step 3 失敗，中止測試")
            return

        self.step4_report(results)


# ═══════════════════════════════════════════════════════════
#  進入點
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    if not preflight_check():
        print("  前置檢查未通過，請修正後再執行。")
        sys.exit(1)

    tester = LocalTester()
    tester.run()
