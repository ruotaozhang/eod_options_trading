# 🥉 Railway 快速部署教程

## 🎯 **为什么选择Railway？**

- ✅ **$5免费额度** (约运行15-30天)
- ✅ **最快部署** (5分钟内完成)
- ✅ 自动CI/CD
- ✅ 内置监控
- ✅ 简单易用

**最适合:** 快速原型、短期测试、即时部署

---

## 📋 **第1步: 准备代码仓库**

### 推送代码到GitHub
```bash
# 如果还没有GitHub仓库
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/eod-options-trading.git
git push -u origin main
```

---

## 🚀 **第2步: 注册Railway**

1. **访问:** https://railway.app/
2. **点击 "Login"**
3. **选择 "Login with GitHub"**
4. **授权Railway访问GitHub**

---

## 📦 **第3步: 创建项目**

### 从GitHub部署
1. **点击 "New Project"**
2. **选择 "Deploy from GitHub repo"**
3. **选择你的交易系统仓库**
4. **点击 "Deploy Now"**

### 配置构建
Railway会自动检测到Python项目并开始构建

---

## 🔧 **第4步: 配置环境变量**

### 设置API密钥
1. **在Railway项目页面点击你的服务**
2. **切换到 "Variables" 标签**
3. **添加环境变量:**
   ```
   ALPACA_API_KEY=your_api_key_here
   ALPACA_SECRET_KEY=your_secret_key_here
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   ```
4. **点击 "Add" 保存每个变量**

---

## 📝 **第5步: 优化配置文件**

### 创建railway.json (可选)
```json
{
    "build": {
        "builder": "nixpacks"
    },
    "deploy": {
        "startCommand": "python main.py",
        "restartPolicyType": "always"
    }
}
```

### 创建Procfile (推荐)
```
worker: python main.py
```

### 创建runtime.txt (指定Python版本)
```
python-3.9.18
```

---

## 🎯 **第6步: 部署和监控**

### 自动部署
- Railway会自动检测代码更改
- 每次推送到GitHub都会自动重新部署

### 查看日志
1. **在Railway项目页面点击你的服务**
2. **切换到 "Deployments" 标签**
3. **点击最新部署查看日志**

### 监控运行状态
1. **在 "Metrics" 标签查看资源使用**
2. **监控CPU和内存使用情况**

---

## 💰 **第7步: 管理免费额度**

### 查看使用情况
1. **点击右上角头像**
2. **选择 "Usage"**
3. **查看当前额度使用情况**

### 优化资源使用
```python
# 在main.py中添加资源优化
import gc
import time

def optimize_memory():
    """定期清理内存"""
    gc.collect()
    
# 在主循环中定期调用
while True:
    # 你的交易逻辑
    time.sleep(300)  # 5分钟
    optimize_memory()
```

---

## 🔄 **第8步: 更新和重启**

### 自动更新
```bash
# 推送更新到GitHub
git add .
git commit -m "Update trading logic"
git push

# Railway会自动重新部署
```

### 手动重启
1. **在Railway项目页面**
2. **点击 "Restart"**

---

## 📊 **第9步: 高级配置**

### 健康检查
```python
# 在你的main.py中添加
import os
from datetime import datetime

def health_check():
    """健康检查端点"""
    with open('/tmp/health', 'w') as f:
        f.write(f"OK - {datetime.now()}")

# 定期调用
health_check()
```

### 优雅关闭
```python
import signal
import sys

def signal_handler(sig, frame):
    print('优雅关闭交易系统...')
    # 关闭所有持仓
    # 保存状态
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

---

## 🆘 **故障排除**

### 常见问题

**1. 构建失败**
```bash
# 检查requirements.txt
# 确保所有依赖都列出
pip freeze > requirements.txt
```

**2. 环境变量问题**
- 确保在Railway面板中正确设置
- 检查变量名拼写
- 确保没有多余空格

**3. 内存不足**
```python
# 减少内存使用
import sys
sys.setrecursionlimit(1000)

# 优化pandas操作
import pandas as pd
pd.options.mode.chained_assignment = None
```

**4. 网络连接问题**
```python
# 添加重试逻辑
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.3)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

---

## 📈 **性能优化**

### 减少资源使用
```python
# 1. 减少日志输出
import logging
logging.getLogger().setLevel(logging.WARNING)

# 2. 优化数据获取频率
# 减少API调用次数

# 3. 使用更高效的数据结构
import numpy as np
# 使用numpy数组而不是Python列表
```

### 监控成本
```bash
# 创建成本监控脚本
echo "当前Railway使用情况:"
echo "查看: https://railway.app/account/usage"
```

---

## 💡 **省钱技巧**

### 1. 仅在交易时间运行
```python
from datetime import datetime
import pytz

def is_trading_hours():
    et_tz = pytz.timezone('America/New_York')
    et_time = datetime.now(et_tz).time()
    
    # 美东时间 9:30-16:00
    start_time = et_time.replace(hour=9, minute=30)
    end_time = et_time.replace(hour=16, minute=0)
    
    return start_time <= et_time <= end_time

# 主循环
while True:
    if is_trading_hours():
        # 运行交易逻辑
        run_trading()
    else:
        # 长时间睡眠
        time.sleep(3600)  # 1小时
```

### 2. 周末暂停
```python
import calendar

def is_weekday():
    return datetime.now().weekday() < 5  # 0-4 是周一到周五

if not is_weekday():
    time.sleep(86400)  # 睡眠24小时
```

### 3. 优化检查频率
```python
# 减少监控频率
position_check_interval = 300  # 5分钟而不是1分钟
signal_check_interval = 60     # 1分钟而不是30秒
```

---

## ✅ **Railway部署检查清单**

- [ ] GitHub仓库创建并推送代码
- [ ] Railway账户注册
- [ ] 项目创建并连接GitHub
- [ ] 环境变量配置正确
- [ ] 构建成功
- [ ] 服务正常运行
- [ ] 日志输出正常
- [ ] 监控设置完成
- [ ] 免费额度监控

🎉 **恭喜！你的交易系统现在在Railway上运行！**

---

## 📞 **获取帮助**

### Railway官方资源:
- 📖 文档: https://docs.railway.app/
- 💬 Discord: https://discord.gg/railway
- 🐛 GitHub: https://github.com/railwayapp/cli

### 常见命令:
```bash
# 安装Railway CLI (可选)
npm install -g @railway/cli

# 登录
railway login

# 部署
railway up

# 查看日志
railway logs

# 查看状态
railway status
```

---

## 💰 **成本估算**

- **免费额度**: $5/月
- **预计运行时间**: 15-30天 (取决于使用强度)
- **每小时成本**: 约$0.01-0.02
- **交易日运行**: 约6.5小时/天
- **月度成本**: 约$4-6 (可能超出免费额度)

**建议**: Railway适合短期测试，长期使用考虑Oracle Cloud

---

## 🔄 **升级选项**

当免费额度用完时:
1. **等待下个月重置** (推荐)
2. **升级到付费计划** ($5+/月)
3. **迁移到其他免费平台** (Oracle Cloud)
4. **使用多个账户** (不推荐)

**最佳策略**: 用Railway做快速原型，确认可行后迁移到Oracle Cloud长期运行 