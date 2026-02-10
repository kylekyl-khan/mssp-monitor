# CrowdStrike MSSP Monitor v2.0

企業級 CrowdStrike Falcon Sensor 多租戶監控系統

## 📚 架構說明

```
┌──────────────────────────────────────────────────────────────┐
│                    CrowdStrike API                            │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Python Monitor (Container)                                  │
│  - 定期抓取各租戶端點數量                                       │
│  - 推送指標到 InfluxDB & Prometheus                           │
└──────────────┬────────────────────────┬─────────────────────┘
               │                        │
               ▼                        ▼
┌──────────────────────┐    ┌──────────────────────┐
│   InfluxDB (TSDB)    │    │  Prometheus (監控)   │
│   - 歷史數據儲存      │    │  - 即時告警         │
│   - 長期趨勢分析      │    │  - 系統健康監控      │
└──────────┬───────────┘    └───────────┬──────────┘
           │                            │
           │        ┌──────────────┐    │
           └────────► Telegraf     ◄────┘
                    │ (資料收集器) │
                    └──────┬───────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │    Grafana      │
                  │  (視覺化平台)    │
                  └─────────────────┘
```

## 🚀 快速開始

### 1. 前置需求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB RAM
- 20GB 可用磁碟空間

### 2. 安裝步驟

```bash
# 1. Clone 專案
git clone <your-repo-url>
cd mssp-monitor-v2

# 2. 複製環境變數範本
cp .env.example .env

# 3. 編輯 .env 檔案，填入真實憑證
nano .env

# 4. 啟動所有服務
docker-compose up -d

# 5. 檢查服務狀態
docker-compose ps
```

### 3. 訪問各服務

| 服務 | URL | 預設帳密 |
|------|-----|---------|
| **Grafana** | http://localhost:3000 | admin / admin123456 |
| **Prometheus** | http://localhost:9090 | 無 |
| **InfluxDB** | http://localhost:8086 | admin / admin123456 |
| **AlertManager** | http://localhost:9093 | 無 |

## 📊 Grafana Dashboard 使用

### 初次登入

1. 訪問 http://localhost:3000
2. 使用帳密：`admin` / `admin123456`
3. Dashboard 已自動載入，路徑：**Home > Dashboards > CrowdStrike > MSSP Monitor**

### Dashboard 功能

#### 📌 Pinned CIDs 總授權使用量
- **線圖**：顯示重點租戶的總端點數趨勢
- **閾值線**：375 台（紅色警戒線）

#### 🎯 授權使用率儀表板
- **Gauge**：實時顯示使用率百分比
- 顏色標示：
  - 綠色：< 80%
  - 黃色：80-95%
  - 橙色：95-100%
  - 紅色：> 100%

#### 🏢 各租戶端點數量趨勢（可多選）
- **變數選擇器**：右上角可多選 CID
- **自動高亮**：Pinned CIDs 線條較粗
- **圖例統計**：顯示最新值、最小值、最大值、平均值

#### 📋 當前所有租戶端點數量
- **表格**：即時顯示所有租戶數據
- **排序**：點擊欄位標題可排序
- **過濾**：支援搜尋功能

## 🔔 告警規則

系統內建以下告警（透過 Prometheus + AlertManager）：

### Critical 級別
- ✅ Pinned CIDs 總數超過 375
- ✅ 監控腳本停止運作
- ✅ InfluxDB 服務停止

### Warning 級別
- ✅ 單一租戶端點數 1 小時內增加 > 20%
- ✅ 單一租戶端點數 1 小時內減少 > 30%
- ✅ CPU 使用率 > 80% 持續 10 分鐘
- ✅ 記憶體使用率 > 85% 持續 10 分鐘
- ✅ 磁碟使用率 > 85%

### 接收告警郵件

編輯 `prometheus/alertmanager.yml`：

```yaml
global:
  smtp_auth_username: 'your_email@gmail.com'
  smtp_auth_password: 'your_app_password'

receivers:
  - name: 'email-notifications'
    email_configs:
      - to: 'your_team@example.com'
```

重啟服務：
```bash
docker-compose restart alertmanager
```

## 🛠️ 常用指令

### 查看日誌
```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務
docker-compose logs -f mssp-monitor
docker-compose logs -f grafana
```

### 重啟服務
```bash
# 重啟單一服務
docker-compose restart mssp-monitor

# 重啟所有服務
docker-compose restart
```

### 停止服務
```bash
# 停止但保留資料
docker-compose stop

# 停止並刪除容器（資料保留在 Volume）
docker-compose down

# 停止並刪除所有資料（危險！）
docker-compose down -v
```

### 更新程式碼
```bash
# 1. 修改程式碼後重新建置
docker-compose build mssp-monitor

# 2. 重啟容器
docker-compose up -d mssp-monitor
```

## 📁 目錄結構

```
mssp-monitor-v2/
├── docker-compose.yml          # Docker 主配置
├── .env                        # 環境變數（敏感資料）
├── .env.example                # 環境變數範本
│
├── app/                        # Python 監控腳本
│   ├── Dockerfile
│   ├── requirements.txt
│   └── monitor.py
│
├── telegraf/                   # Telegraf 配置
│   └── telegraf.conf
│
├── prometheus/                 # Prometheus 配置
│   ├── prometheus.yml
│   ├── alertmanager.yml
│   └── rules/
│       └── alerts.yml
│
├── grafana/                    # Grafana 配置
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasources.yml
│   │   └── dashboards/
│   │       └── dashboards.yml
│   └── dashboards/
│       └── mssp-overview.json
│
└── influxdb/                   # InfluxDB 配置（可選）
```

## 🔧 自訂配置

### 修改檢查間隔

編輯 `.env`：
```bash
CHECK_INTERVAL=1800  # 改為 30 分鐘
```

### 修改授權閾值

編輯 `.env`：
```bash
LICENSE_THRESHOLD=500  # 改為 500 台
```

### 新增 Pinned CIDs

編輯 `.env`：
```bash
PINNED_CIDS=cid1,cid2,cid3,new_cid
```

## 📊 資料保留策略

### InfluxDB
- 預設無限期保留
- 建議設定 30 天保留：
```bash
# 進入 InfluxDB CLI
docker exec -it mssp-influxdb influx

# 設定保留策略
CREATE RETENTION POLICY "30days" ON "crowdstrike" DURATION 30d REPLICATION 1 DEFAULT
```

### Prometheus
- 預設保留 30 天
- 修改保留期間，編輯 `prometheus/prometheus.yml`：
```yaml
command:
  - '--storage.tsdb.retention.time=90d'  # 改為 90 天
```

## 🐛 故障排除

### 問題：InfluxDB 無法連線

```bash
# 檢查 InfluxDB 日誌
docker-compose logs influxdb

# 重啟 InfluxDB
docker-compose restart influxdb
```

### 問題：Grafana 看不到資料

1. 檢查 Data Source 連線狀態：
   - 進入 Grafana > Configuration > Data Sources
   - 測試 InfluxDB 和 Prometheus 連線

2. 檢查 Python 腳本是否正常運行：
```bash
docker-compose logs mssp-monitor
```

### 問題：告警郵件收不到

1. 檢查 AlertManager 配置：
```bash
docker-compose logs alertmanager
```

2. 測試 SMTP 設定（使用 Gmail App Password）

## 📈 效能優化

### 大量租戶優化（100+ CIDs）

1. 增加檢查間隔：
```bash
CHECK_INTERVAL=7200  # 2 小時
```

2. 增加資源限制（`docker-compose.yml`）：
```yaml
services:
  mssp-monitor:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### 降低磁碟使用

1. 縮短資料保留期間（見上方資料保留策略）
2. 定期清理舊日誌：
```bash
docker-compose logs --tail=1000 > backup.log
docker-compose down
docker-compose up -d
```

## 🔒 安全建議

1. ✅ 修改所有預設密碼
2. ✅ 使用強密碼（建議 16+ 字元）
3. ✅ 限制 Grafana 訪問 IP（透過防火牆）
4. ✅ 啟用 HTTPS（使用 Nginx Reverse Proxy）
5. ✅ 定期備份資料庫

## 📦 備份與還原

### 備份
```bash
# 備份所有資料
docker run --rm \
  -v mssp-monitor-v2_influxdb-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/influxdb-$(date +%Y%m%d).tar.gz /data
```

### 還原
```bash
# 還原資料
docker run --rm \
  -v mssp-monitor-v2_influxdb-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/influxdb-20240101.tar.gz -C /
```

## 🆘 支援

- 📧 Email: support@aishield.com.tw
- 📝 Issues: [GitHub Issues](your-repo-url/issues)
- 📚 Documentation: [Wiki](your-repo-url/wiki)

## 📄 授權

MIT License

---

**版本**：v2.0  
**最後更新**：2024-02-09  
**維護者**：AI Shield Security Team
