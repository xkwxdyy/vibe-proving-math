#!/bin/bash
# vibe_proving Docker 快速启动脚本

set -e

echo "🐳 vibe_proving Docker 快速启动"
echo "================================"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误：未检测到 Docker"
    echo "请先安装 Docker：https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 docker-compose 是否可用
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ 错误：未检测到 docker-compose"
    echo "请安装 Docker Compose：https://docs.docker.com/compose/install/"
    exit 1
fi

# 检查配置文件
if [ ! -f "app/config.toml" ]; then
    echo "📝 首次运行：创建配置文件"
    cp app/config.example.toml app/config.toml
    echo ""
    echo "⚠️  请编辑 app/config.toml 文件，至少配置以下内容："
    echo "   [llm]"
    echo "   base_url = \"https://api.deepseek.com/v1\"  # 或其他兼容端点"
    echo "   api_key  = \"sk-your-api-key\"              # 填写您的API密钥"
    echo "   model    = \"deepseek-chat\"                # 或其他模型"
    echo ""
    read -p "按回车键继续（确认已编辑配置文件）... " -r
fi

# 创建数据目录
mkdir -p data

# 构建并启动
echo "🔨 构建 Docker 镜像..."
docker-compose build

echo ""
echo "🚀 启动服务..."
docker-compose up -d

echo ""
echo "⏳ 等待服务就绪..."
sleep 5

# 检查健康状态
if curl -s http://localhost:8080/health > /dev/null; then
    echo ""
    echo "✅ 服务启动成功！"
    echo ""
    echo "📱 访问地址："
    echo "   http://localhost:8080/ui/"
    echo ""
    echo "🛠️  常用命令："
    echo "   查看日志：docker-compose logs -f"
    echo "   停止服务：docker-compose down"
    echo "   重启服务：docker-compose restart"
    echo "   查看状态：docker-compose ps"
    echo ""
else
    echo ""
    echo "⚠️  服务可能未完全启动，请稍后访问："
    echo "   http://localhost:8080/ui/"
    echo ""
    echo "查看日志："
    echo "   docker-compose logs -f"
fi
