@echo off
chcp 65001 >nul
echo ========================================
echo   查看服務日誌
echo ========================================
echo.

REM 檢查容器是否運行
docker-compose ps -q 2>nul | findstr /r "." >nul
if errorlevel 1 (
    echo [!] 沒有發現運行中的容器
    echo [!] 請先執行 start.bat 啟動服務
    echo.
    pause
    exit /b 0
)

echo 選擇要查看的服務：
echo.
echo   1 = 所有服務
echo   2 = Python 監控腳本 (mssp-monitor)
echo   3 = Grafana
echo   4 = InfluxDB
echo   5 = Prometheus
echo   6 = Telegraf
echo   7 = AlertManager
echo   8 = 儲存所有日誌到檔案
echo   9 = 返回
echo.
choice /c 123456789 /n /m "請選擇 [1-9]: "

if errorlevel 9 exit /b 0
if errorlevel 8 goto save_logs
if errorlevel 7 goto alertmanager
if errorlevel 6 goto telegraf
if errorlevel 5 goto prometheus
if errorlevel 4 goto influxdb
if errorlevel 3 goto grafana
if errorlevel 2 goto monitor
if errorlevel 1 goto all

:all
echo.
echo [*] 顯示所有服務日誌（按 Ctrl+C 停止）
echo.
docker-compose logs -f
goto end

:monitor
echo.
echo [*] 顯示 Python 監控腳本日誌（按 Ctrl+C 停止）
echo.
docker-compose logs -f mssp-monitor
goto end

:grafana
echo.
echo [*] 顯示 Grafana 日誌（按 Ctrl+C 停止）
echo.
docker-compose logs -f grafana
goto end

:influxdb
echo.
echo [*] 顯示 InfluxDB 日誌（按 Ctrl+C 停止）
echo.
docker-compose logs -f influxdb
goto end

:prometheus
echo.
echo [*] 顯示 Prometheus 日誌（按 Ctrl+C 停止）
echo.
docker-compose logs -f prometheus
goto end

:telegraf
echo.
echo [*] 顯示 Telegraf 日誌（按 Ctrl+C 停止）
echo.
docker-compose logs -f telegraf
goto end

:alertmanager
echo.
echo [*] 顯示 AlertManager 日誌（按 Ctrl+C 停止）
echo.
docker-compose logs -f alertmanager
goto end

:save_logs
echo.
set filename=mssp-logs-%date:~0,4%%date:~5,2%%date:~8,2%-%time:~0,2%%time:~3,2%%time:~6,2%.txt
set filename=%filename: =0%
echo [*] 正在儲存日誌到 %filename%...
docker-compose logs > %filename% 2>&1
echo [✓] 日誌已儲存到 %filename%
echo.
echo [?] 是否開啟日誌檔案？ (Y/N)
choice /c YN /n
if not errorlevel 2 (
    notepad %filename%
)
goto end

:end
echo.
pause
