#!/bin/bash
# 一键云部署配置脚本

echo "☁️ 云部署配置向导"
echo "===================="

# 选择部署平台
echo "请选择云部署平台:"
echo "1) Oracle Cloud (推荐 - 永久免费)"
echo "2) GitHub Codespaces (最简单)"
echo "3) Railway (快速部署)"
echo "4) 全部配置"

read -p "输入选择 (1-4): " choice

case $choice in
    1)
        echo "🥇 配置Oracle Cloud部署..."
        ;;
    2)
        echo "🥈 配置GitHub Codespaces部署..."
        create_codespaces_config
        ;;
    3)
        echo "🥉 配置Railway部署..."
        create_railway_config
        ;;
    4)
        echo "🔧 配置所有平台..."
        create_codespaces_config
        create_railway_config
        create_docker_config
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

# GitHub Codespaces配置
create_codespaces_config() {
    echo "📂 创建Codespaces配置..."
    
    mkdir -p .devcontainer
    
    # 创建devcontainer.json
    cat > .devcontainer/devcontainer.json << 'EOF'
{
    "name": "EOD Options Trading",
    "image": "mcr.microsoft.com/vscode/devcontainers/miniconda:0-3",
    "features": {
        "ghcr.io/devcontainers/features/github-cli:1": {}
    },
    "postCreateCommand": ".devcontainer/postCreateCommand.sh",
    "customizations": {
        "vscode": {
            "extensions": [
                "ms-python.python",
                "ms-python.flake8",
                "ms-toolsai.jupyter",
                "ms-vscode.vscode-json"
            ],
            "settings": {
                "python.defaultInterpreterPath": "/opt/miniconda/envs/eod_options_trading/bin/python",
                "python.terminal.activateEnvironment": true
            }
        }
    },
    "forwardPorts": [],
    "remoteUser": "vscode"
}
EOF

    # 创建启动后脚本
    cat > .devcontainer/postCreateCommand.sh << 'EOF'
#!/bin/bash
echo "🚀 设置交易系统环境..."

# 创建conda环境
if [ -f environment.yml ]; then
    conda env create -f environment.yml
else
    conda create -n eod_options_trading python=3.9 -y
fi

# 激活环境
source /opt/miniconda/etc/profile.d/conda.sh
conda activate eod_options_trading

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
if [ ! -f .env ]; then
    cp config.env.example .env
    echo "⚠️  请编辑 .env 文件添加API密钥"
fi

echo "✅ 环境设置完成"
echo "📝 下一步: 编辑 .env 文件，然后运行 python main.py"
EOF

    chmod +x .devcontainer/postCreateCommand.sh
    
    # 创建运行脚本
    cat > run_in_codespaces.sh << 'EOF'
#!/bin/bash
# Codespaces中运行交易系统

echo "🚀 启动交易系统 (Codespaces模式)"
echo "=================================="

# 激活conda环境
source /opt/miniconda/etc/profile.d/conda.sh
conda activate eod_options_trading

# 检查配置
if [ ! -f .env ]; then
    echo "❌ 请先配置 .env 文件"
    exit 1
fi

# 显示使用时间提醒
echo "⏰ Codespaces免费额度: 120小时/月"
echo "📊 建议仅在交易时间运行 (美东9:30-16:00)"
echo "=================================="

# 选择运行模式
echo "选择运行模式:"
echo "1) 正常运行 (手动停止)"
echo "2) 限时运行 (3小时后自动停止)"
echo "3) 仅交易时间运行"

read -p "输入选择 (1-3): " mode

case $mode in
    1)
        python main.py
        ;;
    2)
        timeout 3h python main.py
        echo "✅ 3小时运行完成"
        ;;
    3)
        python run_trading_hours.py
        ;;
    *)
        echo "❌ 无效选择，使用默认模式"
        python main.py
        ;;
esac
EOF

    chmod +x run_in_codespaces.sh
    
    echo "✅ Codespaces配置创建完成"
}

# Railway配置
create_railway_config() {
    echo "📂 创建Railway配置..."
    
    # 创建railway.json
    cat > railway.json << 'EOF'
{
    "build": {
        "builder": "nixpacks"
    },
    "deploy": {
        "startCommand": "python main.py",
        "restartPolicyType": "always"
    }
}
EOF

    # 创建Procfile
    cat > Procfile << 'EOF'
worker: python main.py
EOF

    # 创建runtime.txt
    cat > runtime.txt << 'EOF'
python-3.9.18
EOF

    echo "✅ Railway配置创建完成"
}

# Docker配置
create_docker_config() {
    echo "📂 创建Docker配置..."
    
    # 创建Dockerfile
    cat > Dockerfile << 'EOF'
FROM continuumio/miniconda3:latest

WORKDIR /app

# 复制环境文件
COPY environment.yml .
COPY requirements.txt .

# 创建conda环境
RUN conda env create -f environment.yml

# 激活环境并安装依赖
SHELL ["conda", "run", "-n", "eod_options_trading", "/bin/bash", "-c"]
RUN pip install -r requirements.txt

# 复制代码
COPY . .

# 设置环境变量
ENV CONDA_DEFAULT_ENV=eod_options_trading
ENV PATH=/opt/conda/envs/eod_options_trading/bin:$PATH

# 运行交易系统
CMD ["conda", "run", "-n", "eod_options_trading", "python", "main.py"]
EOF

    # 创建docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  trading-bot:
    build: .
    container_name: eod-options-trading
    restart: unless-stopped
    environment:
      - ALPACA_API_KEY=${ALPACA_API_KEY}
      - ALPACA_SECRET_KEY=${ALPACA_SECRET_KEY}
      - ALPACA_BASE_URL=${ALPACA_BASE_URL}
    volumes:
      - ./logs:/app/logs
    env_file:
      - .env
EOF

    # 创建.dockerignore
    cat > .dockerignore << 'EOF'
.git
.gitignore
README.md
Dockerfile
.dockerignore
logs/
__pycache__/
*.pyc
.pytest_cache/
.vscode/
EOF

    echo "✅ Docker配置创建完成"
}

# 创建GitHub Actions工作流
create_github_actions() {
    echo "📂 创建GitHub Actions配置..."
    
    mkdir -p .github/workflows
    
    cat > .github/workflows/deploy.yml << 'EOF'
name: Deploy Trading Bot

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Run tests
      run: |
        python tests/verify_account_connection.py
      env:
        ALPACA_API_KEY: ${{ secrets.ALPACA_API_KEY }}
        ALPACA_SECRET_KEY: ${{ secrets.ALPACA_SECRET_KEY }}
        ALPACA_BASE_URL: ${{ secrets.ALPACA_BASE_URL }}

  deploy-railway:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Railway
      uses: bervProject/railway-deploy@main
      with:
        railway_token: ${{ secrets.RAILWAY_TOKEN }}
        service: trading-bot
EOF

    echo "✅ GitHub Actions配置创建完成"
}

# 创建部署说明
create_deployment_guide() {
    cat > DEPLOYMENT_GUIDE.md << 'EOF'
# 🚀 云部署指南

## 📋 已创建的配置文件

### GitHub Codespaces:
- `.devcontainer/devcontainer.json` - Codespace配置
- `.devcontainer/postCreateCommand.sh` - 自动安装脚本
- `run_in_codespaces.sh` - 运行脚本

### Railway:
- `railway.json` - Railway配置
- `Procfile` - 进程定义
- `runtime.txt` - Python版本

### Docker:
- `Dockerfile` - Docker镜像配置
- `docker-compose.yml` - 容器编排
- `.dockerignore` - 忽略文件

### GitHub Actions:
- `.github/workflows/deploy.yml` - 自动部署

## 🚀 快速开始

### 1. GitHub Codespaces (推荐新手):
1. 将代码推送到GitHub
2. 在仓库页面点击 "Code" → "Codespaces" → "Create codespace"
3. 等待环境设置完成
4. 编辑 `.env` 文件添加API密钥
5. 运行: `./run_in_codespaces.sh`

### 2. Railway (快速部署):
1. 注册Railway账户
2. 连接GitHub仓库
3. 设置环境变量
4. 自动部署

### 3. Oracle Cloud (最佳长期选择):
按照 `oracle_cloud_setup.md` 详细教程操作

## 📞 获取帮助
查看具体平台的详细教程文件
EOF

    echo "✅ 部署指南创建完成"
}

# 主程序执行
case $choice in
    2)
        create_codespaces_config
        ;;
    3)
        create_railway_config
        ;;
    4)
        create_codespaces_config
        create_railway_config
        create_docker_config
        create_github_actions
        ;;
esac

create_deployment_guide

echo ""
echo "🎉 云部署配置完成!"
echo "📖 查看 DEPLOYMENT_GUIDE.md 了解如何使用"
echo "📁 查看 cloud_deployment/ 文件夹中的详细教程"
echo ""
echo "推荐步骤:"
echo "1. 选择一个平台 (推荐Oracle Cloud或GitHub Codespaces)"
echo "2. 按照对应教程设置"
echo "3. 配置API密钥"
echo "4. 开始云端交易!" 