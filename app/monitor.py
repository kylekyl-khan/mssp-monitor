"""
CrowdStrike MSSP Monitor v2.0
支援 InfluxDB + Prometheus 雙寫
"""
import json
import os
import time
import sys
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from falconpy import Hosts, FlightControl, OAuth2
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/data/mssp_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === 從環境變數讀取配置 ===
CONFIG = {
    "client_id": os.getenv("CS_CLIENT_ID"),
    "client_secret": os.getenv("CS_CLIENT_SECRET"),
    "base_url": os.getenv("CS_BASE_URL", "us2"),
    "check_interval": int(os.getenv("CHECK_INTERVAL", "3600")),
    "parent_display_name": os.getenv("PARENT_DISPLAY_NAME", "AISHIELD_HQ"),
    "pinned_cids": [c.strip() for c in os.getenv("PINNED_CIDS", "").split(",") if c.strip()],
    "license_threshold": int(os.getenv("LICENSE_THRESHOLD", "375"))
}

INFLUXDB_CONFIG = {
    "url": os.getenv("INFLUXDB_URL", "http://influxdb:8086"),
    "token": os.getenv("INFLUXDB_TOKEN"),
    "org": os.getenv("INFLUXDB_ORG", "aishield"),
    "bucket": os.getenv("INFLUXDB_BUCKET", "crowdstrike")
}

PROMETHEUS_PUSHGATEWAY = os.getenv("PROMETHEUS_PUSHGATEWAY", "http://prometheus-pushgateway:9091")

STATE_FILE = "/data/mssp_inventory.json"


class MetricsExporter:
    """統一的指標匯出器"""
    
    def __init__(self):
        # InfluxDB 連線
        self.influx_client = InfluxDBClient(
            url=INFLUXDB_CONFIG["url"],
            token=INFLUXDB_CONFIG["token"],
            org=INFLUXDB_CONFIG["org"]
        )
        self.influx_write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        
        # Prometheus Registry
        self.prom_registry = CollectorRegistry()
        self.prom_gauges = {}
        
        logger.info("MetricsExporter 初始化完成")
    
    def write_to_influxdb(self, cid: str, tenant_name: str, count: int, is_pinned: bool, parent_cid: str):
        """寫入 InfluxDB"""
        try:
            point = (
                Point("crowdstrike_hosts")
                .tag("cid", cid)
                .tag("tenant_name", tenant_name)
                .tag("is_pinned", str(is_pinned))
                .tag("parent_cid", parent_cid)
                .field("host_count", count)
                .time(datetime.now(timezone.utc), WritePrecision.NS)
            )
            
            self.influx_write_api.write(
                bucket=INFLUXDB_CONFIG["bucket"],
                org=INFLUXDB_CONFIG["org"],
                record=point
            )
            logger.debug(f"InfluxDB: 寫入 {tenant_name} ({cid}): {count}")
        except Exception as e:
            logger.error(f"InfluxDB 寫入失敗: {e}")
    
    def write_pinned_summary_to_influxdb(self, total: int, threshold: int, over_threshold: bool):
        """寫入 Pinned 總計到 InfluxDB"""
        try:
            point = (
                Point("crowdstrike_pinned_summary")
                .tag("threshold", str(threshold))
                .field("total_count", total)
                .field("over_threshold", int(over_threshold))
                .time(datetime.now(timezone.utc), WritePrecision.NS)
            )
            
            self.influx_write_api.write(
                bucket=INFLUXDB_CONFIG["bucket"],
                org=INFLUXDB_CONFIG["org"],
                record=point
            )
            logger.info(f"InfluxDB: Pinned 總計 {total} (閾值: {threshold})")
        except Exception as e:
            logger.error(f"InfluxDB Pinned 總計寫入失敗: {e}")
    
    def push_to_prometheus(self, metrics_data: Dict):
        """推送到 Prometheus Pushgateway"""
        try:
            # 為每個租戶建立 Gauge
            for cid, data in metrics_data.items():
                # 跳過特殊鍵 _pinned_total
                if cid == '_pinned_total':
                    continue
                    
                gauge_name = f"crowdstrike_host_count"
                if gauge_name not in self.prom_gauges:
                    self.prom_gauges[gauge_name] = Gauge(
                        gauge_name,
                        'CrowdStrike active hosts count',
                        ['cid', 'tenant_name', 'is_pinned'],
                        registry=self.prom_registry
                    )
                
                self.prom_gauges[gauge_name].labels(
                    cid=cid,
                    tenant_name=data['name'],
                    is_pinned=str(data['is_pinned'])
                ).set(data['count'])
            
            # Pinned 總計
            pinned_gauge = Gauge(
                'crowdstrike_pinned_total',
                'Total pinned CIDs host count',
                ['threshold'],
                registry=self.prom_registry
            )
            pinned_gauge.labels(
                threshold=str(CONFIG['license_threshold'])
            ).set(metrics_data.get('_pinned_total', 0))
            
            # 推送到 Pushgateway
            push_to_gateway(
                PROMETHEUS_PUSHGATEWAY,
                job='mssp-monitor',
                registry=self.prom_registry
            )
            logger.info("Prometheus: 指標推送完成")
        except Exception as e:
            logger.error(f"Prometheus 推送失敗: {e}")
    
    def close(self):
        """關閉連線"""
        self.influx_client.close()


class MSSPMonitor:
    """CrowdStrike MSSP 監控系統"""
    
    def __init__(self):
        self.creds = {k: CONFIG[k] for k in ["client_id", "client_secret", "base_url"]}
        self.auth = OAuth2(**self.creds)
        self.fc = FlightControl(**self.creds)
        self.parent_cid = "unknown"
        self.pinned_list = [c.lower() for c in CONFIG.get("pinned_cids", [])]
        self.exporter = MetricsExporter()
        
    def validate_and_setup(self) -> bool:
        """驗證憑證並初始化"""
        try:
            if self.auth.token()["status_code"] != 201:
                logger.error("CrowdStrike 認證失敗")
                return False
            
            temp_hosts = Hosts(**self.creds)
            r = temp_hosts.query_devices_by_filter(limit=1)
            self.parent_cid = r['body']['meta']['pagination'].get('cid', 'unknown').lower()
            logger.info(f"Parent CID: {self.parent_cid}")
            return True
        except Exception as e:
            logger.error(f"初始化失敗: {e}")
            return False
    
    def get_tenants_info(self) -> Dict[str, str]:
        """取得所有租戶資訊"""
        child_cids = set()
        offset = 0
        
        while True:
            id_resp = self.fc.query_children(limit=100, offset=offset)
            ids = id_resp["body"].get("resources", [])
            for cid in ids:
                child_cids.add(cid.lower())
            
            total = id_resp["body"].get("meta", {}).get("pagination", {}).get("total", 0)
            offset += len(ids)
            if offset >= total or not ids:
                break
        
        tenant_map = {}
        cid_list = list(child_cids)
        
        if cid_list:
            for i in range(0, len(cid_list), 100):
                batch = cid_list[i:i+100]
                detail_resp = self.fc.get_children(ids=batch)
                for item in detail_resp["body"].get("resources", []):
                    tenant_map[item["child_cid"].lower()] = item.get("name", item["child_cid"])
        
        final_map = {cid: tenant_map.get(cid, cid) for cid in child_cids}
        final_map[self.parent_cid] = CONFIG["parent_display_name"]
        
        logger.info(f"發現 {len(final_map)} 個租戶")
        return final_map
    
    def fetch_count(self, cid: str) -> int:
        """查詢指定 CID 的活躍端點數"""
        try:
            is_parent = (cid == self.parent_cid)
            hosts_api = Hosts(**self.creds, member_cid=None if is_parent else cid)
            resp = hosts_api.query_devices_by_filter_scroll(filter="last_seen:>'now-7d'", limit=1)
            
            if resp["status_code"] == 200:
                return resp["body"]["meta"]["pagination"]["total"]
            else:
                logger.warning(f"CID {cid} 查詢失敗: {resp['status_code']}")
                return 0
        except Exception as e:
            logger.error(f"查詢 {cid} 時發生錯誤: {e}")
            return 0
    
    def _print_report(self, tenant_map: Dict, new_data: Dict, old_data: Dict, pinned_total_current: int):
        """在 terminal 印出直觀的掃描報告"""
        fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        threshold  = CONFIG['license_threshold']
        over_threshold = pinned_total_current > threshold

        # ── 分類資料 ──────────────────────────────────────────────
        parent_rows, pinned_rows, other_rows = [], [], []

        for cid, name in tenant_map.items():
            current = new_data.get(cid, 0)
            old     = old_data.get(cid, 0)
            change  = current - old
            tag     = "📌 PINNED" if cid in self.pinned_list else ""

            if change > 0:
                change_str = f"+{change} ▲"
            elif change < 0:
                change_str = f"{change} ▼"
            else:
                change_str = "  0  -"

            row = (name, cid, old, current, change_str, tag)

            if cid == self.parent_cid:
                parent_rows.append(row)
            elif cid in self.pinned_list:
                pinned_rows.append(row)
            else:
                other_rows.append(row)

        other_rows.sort(key=lambda x: x[0])   # 依名稱排序

        # ── 表格寬度設定 ──────────────────────────────────────────
        COL = {"name": 32, "cid": 36, "old": 7, "cur": 7, "chg": 8, "tag": 10}
        W   = sum(COL.values()) + len(COL) * 3 + 1   # 總寬度

        def row_str(name, cid, old, cur, chg, tag):
            return (
                f"| {name:<{COL['name']}} "
                f"| {cid:<{COL['cid']}} "
                f"| {old:>{COL['old']}} "
                f"| {cur:>{COL['cur']}} "
                f"| {chg:>{COL['chg']}} "
                f"| {tag:<{COL['tag']}} |"
            )

        sep   = "+" + "+".join("-" * (v + 2) for v in COL.values()) + "+"
        header = row_str("Tenant Name", "CID", "Old", "Now", "Change", "Flag")

        # ── 開始印出 ──────────────────────────────────────────────
        print()
        print("=" * W)
        print(f"  CrowdStrike MSSP 掃描報告　　{fetch_time}")
        print("=" * W)
        print(sep)
        print(header)
        print(sep)

        def print_section(rows, label=None):
            if not rows:
                return
            if label:
                print(f"| {label:<{W - 4}} |")
                print(sep)
            for r in rows:
                print(row_str(*r))
            print(sep)

        print_section(parent_rows, "▶ PARENT")
        print_section(pinned_rows, "▶ PINNED CIDs")
        print_section(other_rows,  "▶ Other Tenants")

        # ── Pinned 授權加總 ───────────────────────────────────────
        status_icon  = "❌ 超過閾值！" if over_threshold else "✅ 正常"
        used_bar_len = 30
        filled       = int(min(pinned_total_current / threshold, 1.0) * used_bar_len)
        bar          = "█" * filled + "░" * (used_bar_len - filled)

        print(f"  📌 Pinned CIDs 授權使用統計")
        print(f"  [{bar}] {pinned_total_current} / {threshold}  {status_icon}")
        print("=" * W)

        # ── 各項推送狀態（稍後由呼叫方填入） ──────────────────────
        print()

    def run_iteration(self):
        """執行一次完整掃描"""
        logger.info("=" * 80)
        logger.info("開始新一輪掃描")

        tenant_map = self.get_tenants_info()

        # 讀取舊狀態
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                old_data = json.load(f)
        else:
            old_data = {}

        new_data               = {}
        metrics_data           = {}
        pinned_total_current   = 0

        # ── 逐一抓取各租戶 ────────────────────────────────────────
        total_tenants = len(tenant_map)
        for idx, (cid, name) in enumerate(tenant_map.items(), start=1):
            # 即時進度提示
            print(f"\r  🔍 抓取中... [{idx}/{total_tenants}] {name[:30]:<30}", end="", flush=True)

            current  = self.fetch_count(cid)
            old      = old_data.get(cid, 0)
            change   = current - old
            is_pinned = cid in self.pinned_list

            new_data[cid] = current
            metrics_data[cid] = {
                'name': name, 'count': current,
                'is_pinned': is_pinned, 'change': change
            }

            # 寫入 InfluxDB（每筆即時寫入）
            self.exporter.write_to_influxdb(
                cid=cid, tenant_name=name, count=current,
                is_pinned=is_pinned, parent_cid=self.parent_cid
            )

            if is_pinned:
                pinned_total_current += current

        print()   # 進度列換行

        # ── 印出完整報告表格 ──────────────────────────────────────
        self._print_report(tenant_map, new_data, old_data, pinned_total_current)

        # ── Pinned 總計寫入 InfluxDB ──────────────────────────────
        threshold      = CONFIG['license_threshold']
        over_threshold = pinned_total_current > threshold
        metrics_data['_pinned_total'] = pinned_total_current

        self.exporter.write_pinned_summary_to_influxdb(
            total=pinned_total_current,
            threshold=threshold,
            over_threshold=over_threshold
        )
        print(f"  [InfluxDB]    ✅ 寫入完成  ({len(new_data)} 筆)")

        # ── 推送 Prometheus ───────────────────────────────────────
        self.exporter.push_to_prometheus(metrics_data)
        print(f"  [Prometheus]  ✅ 推送完成")

        # ── 儲存本機狀態 ──────────────────────────────────────────
        with open(STATE_FILE, "w") as f:
            json.dump(new_data, f, indent=4)
        print(f"  [State File]  ✅ 已儲存至 {STATE_FILE}")

        next_time = datetime.fromtimestamp(
            time.time() + CONFIG['check_interval']
        ).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n  ⏰ 下次掃描時間：{next_time}\n")

        logger.info("掃描完成")
    
    def start(self):
        """啟動監控循環"""
        print()
        print("╔══════════════════════════════════════════╗")
        print("║  CrowdStrike MSSP Monitor  v2.0          ║")
        print("╚══════════════════════════════════════════╝")
        print(f"  Parent CID 驗證中...")

        if not self.validate_and_setup():
            logger.error("初始化失敗，程式退出")
            sys.exit(1)

        print(f"  ✅ 認證成功  Parent CID: {self.parent_cid}")
        print(f"  📋 Pinned CIDs: {len(self.pinned_list)} 個")
        if self.pinned_list:
            for cid in self.pinned_list:
                print(f"        - {cid}")
        print(f"  ⚙️  檢查間隔: {CONFIG['check_interval']} 秒")
        print(f"  ⚠️  授權閾值: {CONFIG['license_threshold']} 台")
        print()

        while True:
            try:
                self.run_iteration()
                time.sleep(CONFIG['check_interval'])
            except KeyboardInterrupt:
                print("\n  🛑 收到中斷信號，正在關閉...\n")
                logger.info("收到中斷信號，正在關閉...")
                self.exporter.close()
                break
            except Exception as e:
                logger.error(f"執行時發生錯誤: {e}", exc_info=True)
                print(f"\n  ❌ 發生錯誤: {e}")
                print(f"  ⏳ 60 秒後重試...\n")
                time.sleep(60)


if __name__ == "__main__":
    monitor = MSSPMonitor()
    monitor.start()
