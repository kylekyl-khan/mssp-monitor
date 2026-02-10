# Windows 環境啟動指南

## 📋 前置需求檢查

### 1. 安裝 Docker Desktop for Windows

#### 下載與安裝
1. 前往 [Docker Desktop 官網](https://www.docker.com/products/docker-desktop/)
2. 下載 Windows 版本
3. 執行安裝程式
4. 安裝過程中會要求啟用 WSL 2（Windows Subsystem for Linux 2）
   - 如果系統提示需要更新 WSL，請按照指示完成

#### 驗證安裝
打開 **PowerShell** 或 **CMD**，執行：
```powershell
docker --version
docker-compose --version
```

應該會看到類似：
```
Docker version 24.0.7, build afdd53b
Docker Compose version v2.23.0
```

### 2. 確保 Docker Desktop 正在運行

- 檢查系統托盤（右下角）是否有 Docker 圖示
- 如果沒有，請啟動 **Docker Desktop** 應用程式
- 等待 Docker 引擎啟動（圖示不再轉動）

---

## 🚀 啟動專案

### 方法一：使用 PowerShell 腳本（推薦）

1. **開啟 PowerShell**
   - 按 `Win + X`，選擇 **"Windows PowerShell"** 或 **"終端機"**
   - 或在開始選單搜尋 "PowerShell"

2. **切換到專案目錄**
   ```powershell
   cd C:\path\to\mssp-monitor-v2
   ```
   例如：
   ```powershell
   cd C:\Users\YourName\Downloads\mssp-monitor-v2
   ```

3. **檢查 .env 檔案**
   ```powershell
   notepad .env
   ```
   確認以下內容已正確填寫：
   - `CS_CLIENT_ID` - CrowdStrike Client ID
   - `CS_CLIENT_SECRET` - CrowdStrike Client Secret
   - `SMTP_USER` - Email 帳號
   - `SMTP_PASSWORD` - Email App Password
   - `INFLUXDB_ADMIN_TOKEN` - 建議改成更安全的隨機字串

4. **啟動所有服務**
   ```powershell
   docker-compose up -d
   ```

5. **查看服務狀態**
   ```powershell
   docker-compose ps
   ```

   你應該會看到類似：
   ```
   NAME                    STATUS              PORTS
   mssp-grafana           Up 30 seconds       0.0.0.0:3000->3000/tcp
   mssp-influxdb          Up 30 seconds       0.0.0.0:8086->8086/tcp
   mssp-monitor           Up 30 seconds       
   mssp-prometheus        Up 30 seconds       0.0.0.0:9090->9090/tcp
   mssp-telegraf          Up 30 seconds       
   mssp-pushgateway       Up 30 seconds       0.0.0.0:9091->9091/tcp
   mssp-alertmanager      Up 30 seconds       0.0.0.0:9093->9093/tcp
   ```

### 方法二：使用 Windows 批次檔

如果你想要一鍵啟動，建立一個 `start.bat` 檔案：

**建立 start.bat**：
```batch
@echo off
echo ========================================
echo   CrowdStrike MSSP Monitor v2.0
echo ========================================
echo.

REM 檢查 Docker 是否運行
docker info >nul 2>&1
if errorlevel 1 (
    echo [錯誤] Docker Desktop 未運行，請先啟動 Docker Desktop
    pause
    exit /b 1
)

echo [檢查] Docker 運行中...
echo.

REM 檢查 .env 檔案
if not exist .env (
    echo [錯誤] 找不到 .env 檔案
    echo [提示] 請複製 .env.example 為 .env 並填入憑證
    pause
    exit /b 1
)

echo [檢查] .env 檔案存在
echo.

REM 啟動服務
echo [啟動] 正在啟動所有服務...
docker-compose up -d

echo.
echo [等待] 服務啟動中...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo   服務狀態
echo ========================================
docker-compose ps

echo.
echo ========================================
echo   訪問服務
echo ========================================
echo   Grafana:      http://localhost:3000
echo                 帳號: admin / admin123456
echo.
echo   Prometheus:   http://localhost:9090
echo   InfluxDB:     http://localhost:8086
echo   AlertManager: http://localhost:9093
echo ========================================
echo.
echo 按任意鍵關閉視窗...
pause >nul
```

然後直接雙擊 `start.bat` 即可啟動！

---

## 🌐 訪問服務

啟動成功後，在瀏覽器中訪問：

### Grafana（主要監控介面）
- **URL**: http://localhost:3000
- **帳號**: admin
- **密碼**: admin123456

#### 首次登入步驟：
1. 開啟瀏覽器
2. 訪問 http://localhost:3000
3. 輸入帳密登入
4. 點擊左側選單 **☰ → Dashboards**
5. 選擇 **CrowdStrike → MSSP Monitor**

### 其他服務
- **Prometheus**: http://localhost:9090
- **InfluxDB**: http://localhost:8086
- **AlertManager**: http://localhost:9093

---

## 📊 查看日誌

### 查看所有服務日誌
```powershell
docker-compose logs -f
```
按 `Ctrl + C` 停止查看

### 查看特定服務日誌
```powershell
# 查看監控腳本日誌
docker-compose logs -f mssp-monitor

# 查看 Grafana 日誌
docker-compose logs -f grafana

# 查看 InfluxDB 日誌
docker-compose logs -f influxdb
```

---

## 🛑 停止服務

### 暫時停止（保留資料）
```powershell
docker-compose stop
```

### 完全停止並移除容器（保留資料）
```powershell
docker-compose down
```

### 重新啟動
```powershell
docker-compose restart
```

### 停止並刪除所有資料（危險！）
```powershell
docker-compose down -v
```

---

## 🔧 常見問題排除

### ❌ 問題 1: "docker: command not found" 或 "無法辨識 docker"

**原因**: Docker Desktop 未安裝或未加入 PATH

**解決方式**:
1. 確認 Docker Desktop 已安裝
2. 重新啟動電腦
3. 確認 Docker Desktop 正在運行（系統托盤有圖示）

### ❌ 問題 2: "Cannot connect to the Docker daemon"

**原因**: Docker Desktop 未運行

**解決方式**:
1. 啟動 Docker Desktop 應用程式
2. 等待 Docker 引擎完全啟動（約 30 秒）
3. 再次執行指令

### ❌ 問題 3: 連接埠被占用 (Port already in use)

**錯誤訊息**:
```
Error: bind: address already in use
```

**解決方式**:

**方法 1: 修改連接埠**
編輯 `docker-compose.yml`，修改衝突的 port：
```yaml
services:
  grafana:
    ports:
      - "3001:3000"  # 改用 3001
```

**方法 2: 停止佔用連接埠的程式**
```powershell
# 查看誰在使用 3000 port
netstat -ano | findstr :3000

# 停止該程序（替換 PID 為實際的 Process ID）
taskkill /PID <PID> /F
```

### ❌ 問題 4: WSL 2 相關錯誤

**錯誤訊息**:
```
WSL 2 installation is incomplete
```

**解決方式**:
1. 開啟 PowerShell（以系統管理員身分）
2. 執行：
   ```powershell
   wsl --install
   ```
3. 重新啟動電腦
4. 再次啟動 Docker Desktop

### ❌ 問題 5: Grafana 無法訪問

**檢查步驟**:
1. 確認服務運行中：
   ```powershell
   docker-compose ps
   ```
   
2. 檢查 Grafana 日誌：
   ```powershell
   docker-compose logs grafana
   ```

3. 測試連線：
   ```powershell
   curl http://localhost:3000
   ```

### ❌ 問題 6: Python 監控腳本一直重啟

**檢查步驟**:
1. 查看日誌找出錯誤：
   ```powershell
   docker-compose logs mssp-monitor
   ```

2. 常見錯誤：
   - **認證失敗**: 檢查 `.env` 中的 `CS_CLIENT_ID` 和 `CS_CLIENT_SECRET`
   - **InfluxDB 連線失敗**: 等待 InfluxDB 完全啟動（約 1 分鐘）

3. 手動重啟：
   ```powershell
   docker-compose restart mssp-monitor
   ```

---

## 🔄 更新程式碼

當你修改了程式碼（例如 `monitor.py`）後：

```powershell
# 1. 重新建置映像檔
docker-compose build mssp-monitor

# 2. 重啟容器
docker-compose up -d mssp-monitor

# 3. 查看日誌確認
docker-compose logs -f mssp-monitor
```

---

## 💾 資料備份

### 備份 InfluxDB 資料

```powershell
# 建立備份目錄
mkdir backups

# 備份
docker run --rm -v mssp-monitor-v2_influxdb-data:/data -v ${PWD}/backups:/backup alpine tar czf /backup/influxdb-backup.tar.gz /data
```

### 還原 InfluxDB 資料

```powershell
# 還原
docker run --rm -v mssp-monitor-v2_influxdb-data:/data -v ${PWD}/backups:/backup alpine tar xzf /backup/influxdb-backup.tar.gz -C /
```

---

## 📝 進階配置

### 修改環境變數

1. **編輯 .env 檔案**
   ```powershell
   notepad .env
   ```

2. **修改後重啟服務**
   ```powershell
   docker-compose down
   docker-compose up -d
   ```

### 查看資源使用狀況

```powershell
# 查看容器資源使用
docker stats

# 查看磁碟使用
docker system df
```

### 清理未使用的資源

```powershell
# 清理未使用的映像檔、容器、網路
docker system prune -a

# 清理未使用的 Volume（注意：會刪除資料！）
docker volume prune
```

---

## 🎯 快速參考指令表

| 操作 | 指令 |
|------|------|
| **啟動所有服務** | `docker-compose up -d` |
| **停止所有服務** | `docker-compose down` |
| **查看服務狀態** | `docker-compose ps` |
| **查看所有日誌** | `docker-compose logs -f` |
| **重啟服務** | `docker-compose restart` |
| **重新建置** | `docker-compose build` |
| **進入容器** | `docker exec -it mssp-monitor bash` |
| **清理系統** | `docker system prune -a` |

---

## 🆘 還是有問題？

1. **檢查 Docker Desktop 狀態**
   - 打開 Docker Desktop
   - 查看 "Containers" 分頁
   - 確認所有容器都是綠色（Running）

2. **完整重啟**
   ```powershell
   docker-compose down -v
   docker-compose up -d
   ```

3. **查看完整日誌**
   ```powershell
   docker-compose logs > logs.txt
   notepad logs.txt
   ```

4. **聯絡支援**
   - 提供 `logs.txt` 內容
   - 說明遇到的錯誤訊息

---

## ✅ 啟動成功確認清單

- [ ] Docker Desktop 正在運行
- [ ] `.env` 檔案已正確配置
- [ ] 執行 `docker-compose up -d` 無錯誤
- [ ] 執行 `docker-compose ps` 所有服務都是 "Up"
- [ ] 可以訪問 http://localhost:3000
- [ ] Grafana 登入成功
- [ ] Dashboard 有資料顯示

全部打勾就代表啟動成功！🎉
