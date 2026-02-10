@echo off
chcp 65001 >nul
echo ========================================
echo   停止 MSSP Monitor 服務
echo ========================================
echo.

REM 檢查是否有容器在運行
docker-compose ps -q 2>nul | findstr /r "." >nul
if errorlevel 1 (
    echo [!] 沒有發現運行中的容器
    echo.
    pause
    exit /b 0
)

echo [!] 發現以下運行中的服務：
echo.
docker-compose ps
echo.

echo [?] 選擇停止方式：
echo     1 = 暫時停止（保留資料）
echo     2 = 停止並移除容器（保留資料）
echo     3 = 完全清除（包含資料，危險！）
echo     4 = 取消
echo.
choice /c 1234 /n /m "請選擇 [1-4]: "

if errorlevel 4 (
    echo.
    echo [!] 已取消
    pause
    exit /b 0
)

if errorlevel 3 (
    echo.
    echo [!] 警告：這將刪除所有資料（包含歷史記錄）！
    echo [?] 確定要繼續嗎？ (Y/N)
    choice /c YN /n
    if errorlevel 2 (
        echo [!] 已取消
        pause
        exit /b 0
    )
    echo.
    echo [*] 正在停止服務並刪除所有資料...
    docker-compose down -v
    goto done
)

if errorlevel 2 (
    echo.
    echo [*] 正在停止服務並移除容器...
    docker-compose down
    goto done
)

if errorlevel 1 (
    echo.
    echo [*] 正在暫時停止服務...
    docker-compose stop
    goto done
)

:done
echo.
if errorlevel 1 (
    echo [X] 操作失敗
    pause
    exit /b 1
)

echo [✓] 操作完成
echo.
echo [!] 提示：
echo     - 重新啟動：執行 start.bat 或 docker-compose up -d
echo.
pause
