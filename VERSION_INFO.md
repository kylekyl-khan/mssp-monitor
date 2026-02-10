# CrowdStrike MSSP Monitor v2.0 - 修正版
## 最後更新：2026-02-10

---

## ✅ 已套用的所有修正

### 1. Docker Compose 修正
- ✅ 移除過時的 `version: '3.8'` 欄位
- ✅ 解決循環依賴問題（prometheus ↔ telegraf）
- ✅ 移除 Prometheus 對 Telegraf 的 depends_on
- ✅ 移除 Telegraf 對 Prometheus 的 depends_on

### 2. Telegraf 配置修正
- ✅ 移除 Docker 插件的過時選項：
  - `container_names = []`
  - `perdevice = true`
  - `total = false`
- ✅ 移除不需要的 `influxdb_v2_listener` 插件
- ✅ 移除不存在的 `max_line_size` 選項

### 3. Monitor.py 功能增強
- ✅ 新增即時進度顯示（`🔍 抓取中... [5/12] 租戶名稱`）
- ✅ 新增格式化表格報告（包含 Parent / Pinned / Other 分類）
- ✅ 新增視覺化進度條（授權使用率）
- ✅ 新增推送狀態確認訊息
- ✅ 新增下次掃描時間提示
- ✅ 改善啟動畫面與錯誤處理

---

## 📦 專案結構（完整檔案清單）

```
mssp-monitor-v2/
│
├── 📄 .env                          # 環境變數（已填入你的憑證）
├── 📄 .env.example                  # 環境變數範本
├── 📄 .gitignore                    # Git 忽略清單
│
├── 📘 README.md                     # 專案說明與部署指南
├── 📘 WINDOWS_SETUP_GUIDE.md        # Windows 詳細啟動指南
├── 📘 ARCHITECTURE.md               # 架構詳解文件
├── 📘 FIX_DEPENDENCY_CYCLE.md       # 循環依賴修正說明
│
├── 🐳 docker-compose.yml            # Docker Compose 主配置（已修正）
│
├── 🚀 start.bat                     # Windows 一鍵啟動腳本
├── 🚀 start.sh                      # Linux/Mac 啟動腳本
├── 🛑 stop.bat                      # Windows 停止腳本
├── 📋 view-logs.bat                 # Windows 日誌查看工具
│
├── app/                             # Python 監控腳本
│   ├── 🐍 monitor.py                # 主程式（v2.0，已增強輸出）
│   ├── 📦 requirements.txt          # Python 依賴清單
│   └── 🐳 Dockerfile                # Python 容器建置檔
│
├── telegraf/                        # Telegraf 配置
│   └── ⚙️ telegraf.conf             # Telegraf 設定（已修正）
│
├── prometheus/                      # Prometheus 配置
│   ├── ⚙️ prometheus.yml            # Prometheus 主配置
│   ├── 📧 alertmanager.yml          # AlertManager 郵件設定
│   └── rules/
│       └── 🔔 alerts.yml            # 告警規則定義
│
└── grafana/                         # Grafana 配置
    ├── provisioning/
    │   ├── datasources/
    │   │   └── 🔌 datasources.yml   # 自動配置資料源
    │   └── dashboards/
    │       └── 📊 dashboards.yml    # 自動載入 Dashboard
    └── dashboards/
        └── 📈 mssp-overview.json    # CrowdStrike MSSP 監控儀表板
```

**總計：22 個檔案**

---

## 🎯 這個版本可以直接使用

這個專案包已經：

✅ 修正所有已知錯誤  
✅ 通過語法檢查  
✅ 包含完整文件  
✅ 包含 Windows 批次檔  
✅ 預先填入你的 CrowdStrike 憑證  

---

## 🚀 快速啟動（3 步驟）

### Windows:

```powershell
# 1. 解壓縮到任意位置
# 2. 確認 Docker Desktop 正在運行
# 3. 雙擊 start.bat
```

### 或使用命令列:

```powershell
cd mssp-monitor-v2
docker-compose up -d
```

---

## 🌐 訪問服務

啟動後訪問：

| 服務 | URL | 帳密 |
|------|-----|------|
| **Grafana** | http://localhost:3000 | admin / admin123456 |
| Prometheus | http://localhost:9090 | - |
| InfluxDB | http://localhost:8086 | admin / admin123456 |

---

## 📝 重要提醒

### 1. 第一次啟動需要時間
- InfluxDB 初始化：約 30 秒
- Grafana 載入 Dashboard：約 10 秒
- Monitor.py 第一次掃描：視租戶數量而定

### 2. 確認服務正常
```powershell
docker-compose ps
```
所有服務的 STATUS 都應該是 **Up**

### 3. 查看監控輸出
```powershell
docker-compose logs -f mssp-monitor
```

### 4. 如果有問題
- 查看 `WINDOWS_SETUP_GUIDE.md` 的故障排除章節
- 查看 `FIX_DEPENDENCY_CYCLE.md` 瞭解已修正的問題
- 使用 `view-logs.bat` 查看各服務日誌

---

## 📞 需要協助？

所有文件都已包含在專案中：
- 不知道怎麼啟動 → `WINDOWS_SETUP_GUIDE.md`
- 想瞭解架構 → `ARCHITECTURE.md`
- 遇到循環依賴錯誤 → `FIX_DEPENDENCY_CYCLE.md`
- 一般使用說明 → `README.md`

---

## 🎉 版本資訊

- **版本**：v2.0 (修正版)
- **建置日期**：2026-02-10
- **修正項目**：3 項（Docker Compose、Telegraf、Monitor.py）
- **狀態**：✅ 可立即部署

---

**享受你的監控系統！** 🚀
