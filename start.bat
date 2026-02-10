@echo off
chcp 65001 >nul
echo ========================================
echo   CrowdStrike MSSP Monitor v2.0
echo ========================================
echo.

REM 檢查 Docker 是否運行
docker info >nul 2>&1
if errorlevel 1 (
    echo [X] Docker Desktop 未運行
    echo [!] 請先啟動 Docker Desktop，然後再執行此腳本
    echo.
    pause
    exit /b 1
)

echo [✓] Docker 運行中
echo.

REM 檢查 .env 檔案
if not exist .env (
    echo [X] 找不到 .env 檔案
    echo.
    if exist .env.example (
        echo [!] 正在從 .env.example 建立 .env...
        copy .env.example .env >nul
        echo [✓] .env 檔案已建立
        echo.
        echo [!] 請編輯 .env 檔案並填入正確的憑證：
        echo     - CS_CLIENT_ID
        echo     - CS_CLIENT_SECRET
        echo     - SMTP_USER
        echo     - SMTP_PASSWORD
        echo.
        echo [?] 是否現在開啟 .env 進行編輯？ (Y/N)
        choice /c YN /n
        if errorlevel 2 goto skip_edit
        notepad .env
        echo.
        echo [?] 憑證已填寫完成？可以繼續嗎？ (Y/N)
        choice /c YN /n
        if errorlevel 2 (
            echo.
            echo [!] 請完成 .env 設定後再次執行此腳本
            pause
            exit /b 1
        )
        :skip_edit
    ) else (
        echo [X] 也找不到 .env.example 範本檔案
        pause
        exit /b 1
    )
)

echo [✓] .env 檔案存在
echo.

REM 檢查是否已有容器在運行
docker-compose ps -q 2>nul | findstr /r "." >nul
if not errorlevel 1 (
    echo [!] 發現已有容器在運行
    echo [?] 是否要重新啟動？ (Y/N)
    choice /c YN /n
    if not errorlevel 2 (
        echo.
        echo [*] 正在停止舊容器...
        docker-compose down
        echo.
    )
)

REM 啟動服務
echo [*] 正在啟動所有服務...
echo.
docker-compose up -d

if errorlevel 1 (
    echo.
    echo [X] 啟動失敗！
    echo [!] 請檢查上方錯誤訊息
    echo.
    pause
    exit /b 1
)

echo.
echo [*] 等待服務啟動中...
timeout /t 15 /nobreak >nul

echo.
echo ========================================
echo   服務狀態
echo ========================================
docker-compose ps

echo.
echo ========================================
echo   訪問服務
echo ========================================
echo.
echo   📈 Grafana (主監控介面)
echo      URL:  http://localhost:3000
echo      帳號: admin
echo      密碼: admin123456
echo.
echo   🔥 Prometheus
echo      URL:  http://localhost:9090
echo.
echo   💾 InfluxDB
echo      URL:  http://localhost:8086
echo.
echo   🔔 AlertManager
echo      URL:  http://localhost:9093
echo.
echo ========================================
echo.
echo [✓] 啟動完成！
echo.
echo [!] 提示：
echo     - 查看日誌：docker-compose logs -f
echo     - 停止服務：docker-compose down
echo     - 重新啟動：docker-compose restart
echo.
echo [?] 是否現在開啟 Grafana？ (Y/N)
choice /c YN /n
if not errorlevel 2 (
    start http://localhost:3000
)

echo.
echo 按任意鍵關閉此視窗...
pause >nul
