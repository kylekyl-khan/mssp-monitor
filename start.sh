#!/bin/bash
# MSSP Monitor 快速啟動腳本

set -e

echo "=========================================="
echo "  CrowdStrike MSSP Monitor v2.0"
echo "=========================================="
echo ""

# 檢查 .env 檔案
if [ ! -f .env ]; then
    echo "❌ 找不到 .env 檔案"
    echo "📝 正在建立 .env 範本..."
    cp .env.example .env
    echo "✅ 已建立 .env 檔案"
    echo ""
    echo "⚠️  請編輯 .env 檔案並填入真實的憑證："
    echo "   - CrowdStrike API 憑證"
    echo "   - Email 設定"
    echo "   - InfluxDB Token"
    echo ""
    echo "編輯完成後請再次執行此腳本。"
    exit 1
fi

# 檢查必要環境變數
echo "🔍 檢查環境變數..."
source .env

if [ -z "$CS_CLIENT_ID" ] || [ "$CS_CLIENT_ID" = "your_client_id_here" ]; then
    echo "❌ 請在 .env 檔案中設定 CS_CLIENT_ID"
    exit 1
fi

if [ -z "$CS_CLIENT_SECRET" ] || [ "$CS_CLIENT_SECRET" = "your_client_secret_here" ]; then
    echo "❌ 請在 .env 檔案中設定 CS_CLIENT_SECRET"
    exit 1
fi

echo "✅ 環境變數檢查通過"
echo ""

# 檢查 Docker
echo "🐳 檢查 Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo "❌ Docker daemon 未運行，請啟動 Docker"
    exit 1
fi

echo "✅ Docker 檢查通過"
echo ""

# 檢查 Docker Compose
echo "🔧 檢查 Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝"
    exit 1
fi

echo "✅ Docker Compose 檢查通過"
echo ""

# 建立必要目錄
echo "📁 建立資料目錄..."
mkdir -p prometheus/rules
mkdir -p grafana/dashboards
mkdir -p grafana/provisioning/{datasources,dashboards}
echo "✅ 目錄建立完成"
echo ""

# 啟動服務
echo "🚀 啟動服務..."
docker-compose up -d

echo ""
echo "⏳ 等待服務啟動..."
sleep 10

# 檢查服務狀態
echo ""
echo "📊 服務狀態："
docker-compose ps

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "訪問以下服務："
echo "  📈 Grafana:      http://localhost:3000"
echo "     帳號: admin / admin123456"
echo ""
echo "  🔥 Prometheus:   http://localhost:9090"
echo "  💾 InfluxDB:     http://localhost:8086"
echo "  🔔 AlertManager: http://localhost:9093"
echo ""
echo "📝 查看日誌："
echo "  docker-compose logs -f"
echo ""
echo "🛑 停止服務："
echo "  docker-compose down"
echo ""
