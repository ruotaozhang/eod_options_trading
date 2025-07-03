# 🥈 GitHub Codespaces 部署教程

## 🎯 **为什么选择GitHub Codespaces？**

- ✅ **120小时/月免费** (约每天4小时)
- ✅ **一键启动**，无需配置服务器
- ✅ 直接从GitHub仓库运行
- ✅ 预装Python环境
- ✅ 最简单的云部署方式

**最适合:** 开发测试、短期运行、快速原型

---

## 📋 **第1步: 准备GitHub仓库**

### 创建GitHub仓库

1. **访问GitHub:** https://github.com/
2. **登录账户** (如果没有，请先注册)
3. **创建新仓库:**
   - 点击右上角 "+" → "New repository"
   - Repository name: `eod-options-trading`
   - 选择 Public 或 Private
   - 点击 "Create repository"

### 上传代码到GitHub

**方式1: 使用GitHub网页界面**
```bash
# 在本地项目目录运行
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/eod-options-trading.git
git push -u origin main
```

**方式2: 直接拖拽上传**
- 将本地项目文件夹中的所有文件选中
- 拖拽到GitHub仓库页面
- 添加提交信息，点击 "Commit changes"

---

## 🚀 **第2步: 启动Codespaces**

### 创建Codespace

1. **打开你的GitHub仓库**
2. **点击绿色的 "Code" 按钮**
3. **选择 "Codespaces" 标签**
4. **点击 "Create codespace on main"**

⏰ **等待启动** (通常1-2分钟)

### 验证环境
```bash
# 检查Python版本
python --version

# 检查当前目录
pwd
ls -la

# 检查conda是否可用
conda --version
```

---

## 🔧 **第3步: 配置环境**

### 创建conda环境
```bash
# 如果没有environment.yml，创建conda环境
conda create -n eod_options_trading python=3.9 -y
conda activate eod_options_trading

# 或者使用现有的environment.yml
conda env create -f environment.yml
conda activate eod_options_trading
```

### 安装依赖
```bash
# 安装Python包
pip install -r requirements.txt

# 验证安装
pip list | grep alpaca
```

### 配置环境变量
```bash
# 复制配置文件
cp config.env.example .env

# 编辑配置文件
code .env
```

**在.env文件中添加你的API密钥:**
```env
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

---

## 🎯 **第4步: 测试系统**

### 快速测试
```bash
# 测试API连接
python tests/verify_account_connection.py

# 测试市场数据
python -c "
from src.data.market_data import MarketDataProvider
market_data = MarketDataProvider()
price = market_data.get_current_price('SPY')
print(f'SPY Price: ${price:.2f}')
"
```

### 短期运行测试
```bash
# 运行系统 (按Ctrl+C停止)
python main.py
```

---

## ⚡ **第5步: 长期运行策略**

由于Codespaces有120小时/月的限制，以下是几种策略：

### 策略1: 分时段运行
```bash
# 创建定时运行脚本
cat > run_scheduled.sh << 'EOF'
#!/bin/bash
echo "开始运行交易系统: $(date)"
timeout 3h python main.py
echo "运行结束: $(date)"
EOF

chmod +x run_scheduled.sh
```

### 策略2: 仅在交易时间运行
```bash
# 创建交易时间检查脚本
cat > run_trading_hours.py << 'EOF'
#!/usr/bin/env python3
from datetime import datetime
import pytz
import subprocess
import time

def is_trading_hours():
    et_tz = pytz.timezone('America/New_York')
    et_time = datetime.now(et_tz).time()
    
    # 美东时间 9:30-16:00
    start_time = et_time.replace(hour=9, minute=30, second=0)
    end_time = et_time.replace(hour=16, minute=0, second=0)
    
    return start_time <= et_time <= end_time

def main():
    print(f"检查交易时间: {datetime.now()}")
    
    if is_trading_hours():
        print("✅ 交易时间，启动系统")
        subprocess.run(['python', 'main.py'])
    else:
        print("❌ 非交易时间，等待中...")
        time.sleep(300)  # 等待5分钟后重新检查

if __name__ == "__main__":
    main()
EOF

chmod +x run_trading_hours.py
```

### 策略3: 后台运行 + 定期检查
```bash
# 后台运行
nohup python main.py > trading.log 2>&1 &

# 保存进程ID
echo $! > trading_bot.pid

# 检查状态
tail -f trading.log
```

---

## 📊 **第6步: 监控和管理**

### 查看使用时间
```bash
# 检查Codespace使用情况
# 在GitHub Settings > Billing > Codespaces 查看
```

### 管理运行状态
```bash
# 查看运行状态
ps aux | grep python

# 停止程序
pkill -f "python main.py"

# 查看日志
tail -f trading.log
```

### 定期保存工作
```bash
# 提交更改到GitHub
git add .
git commit -m "Update logs and config"
git push
```

---

## 🔄 **第7步: 自动化设置**

### 创建启动脚本
```bash
cat > .devcontainer/postCreateCommand.sh << 'EOF'
#!/bin/bash
# Codespace启动后自动执行

echo "🚀 设置交易系统环境..."

# 激活conda环境
conda activate eod_options_trading

# 安装依赖
pip install -r requirements.txt

# 检查配置
if [ ! -f .env ]; then
    cp config.env.example .env
    echo "⚠️  请编辑 .env 文件添加API密钥"
fi

echo "✅ 环境设置完成"
echo "📝 下一步: 编辑 .env 文件，然后运行 python main.py"
EOF

chmod +x .devcontainer/postCreateCommand.sh
```

### 创建devcontainer配置
```bash
mkdir -p .devcontainer

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
                "ms-toolsai.jupyter"
            ]
        }
    },
    "forwardPorts": [],
    "remoteUser": "vscode"
}
EOF
```

---

## 💡 **第8步: 优化技巧**

### 节省使用时间
```bash
# 1. 只在需要时启动
# 2. 设置自动停止
timeout 2h python main.py

# 3. 使用轻量级监控
watch -n 60 'ps aux | grep python'
```

### 快速重启
```bash
# 创建一键重启脚本
cat > restart.sh << 'EOF'
#!/bin/bash
pkill -f "python main.py"
sleep 2
nohup python main.py > trading.log 2>&1 &
echo "系统已重启，PID: $!"
EOF

chmod +x restart.sh
```

### 数据备份
```bash
# 定期备份日志
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz logs/

# 上传到GitHub
git add .
git commit -m "Backup logs $(date)"
git push
```

---

## 🆘 **故障排除**

### 常见问题

**1. 120小时用完了**
```bash
# 等待下个月重置，或者考虑升级账户
# 临时解决: 使用其他免费平台
```

**2. 环境重置**
```bash
# Codespace有时会重置环境
conda activate eod_options_trading
pip install -r requirements.txt
```

**3. 连接超时**
```bash
# 检查网络连接
ping google.com

# 重启Codespace
# 在GitHub页面停止并重新启动
```

**4. 文件丢失**
```bash
# 确保及时提交代码
git add .
git commit -m "Save progress"
git push
```

---

## ⚡ **高级技巧**

### 多环境管理
```bash
# 开发环境
conda create -n dev python=3.9
conda activate dev

# 生产环境
conda create -n prod python=3.9
conda activate prod
```

### 远程调试
```bash
# 使用VS Code的调试功能
# 设置断点，逐步调试代码
```

### 性能监控
```bash
# 创建监控脚本
cat > monitor.py << 'EOF'
import psutil
import time

def monitor_system():
    while True:
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        print(f"CPU: {cpu}%, Memory: {memory}%")
        time.sleep(60)

if __name__ == "__main__":
    monitor_system()
EOF
```

---

## ✅ **Codespaces部署检查清单**

- [ ] GitHub账户和仓库创建
- [ ] 代码上传到GitHub
- [ ] Codespace启动成功
- [ ] Conda环境配置
- [ ] 依赖包安装完成
- [ ] API密钥配置正确
- [ ] 系统测试通过
- [ ] 监控脚本设置
- [ ] 自动化脚本配置
- [ ] 数据备份策略

🎉 **恭喜！你的交易系统现在在Codespaces中运行！**

---

## 📈 **使用建议**

### 最佳实践:
1. **合理分配时间**: 每天最多4小时
2. **专注交易时间**: 美东9:30-16:00运行
3. **定期保存**: 及时提交代码到GitHub
4. **监控使用量**: 关注剩余时间
5. **准备备选**: 配合其他免费平台使用

### 成本估算:
- **免费额度**: 120小时/月
- **交易日**: 约21天/月
- **每日可用**: 约5.7小时/天
- **交易时间**: 6.5小时/天 (刚好够用!)

**完美匹配交易需求！** 🎯 