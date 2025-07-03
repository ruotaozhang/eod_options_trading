# 🥇 Oracle Cloud 免费部署教程

## 🎯 **为什么选择Oracle Cloud？**

- ✅ **永久免费** (不是试用期)
- ✅ 1GB RAM + 1 OCPU (足够运行交易系统)
- ✅ 24/7无限制运行
- ✅ 网络稳定，延迟低
- ✅ 最适合生产环境

---

## 📋 **第1步: 注册Oracle Cloud账户**

1. **访问:** https://www.oracle.com/cloud/free/
2. **点击:** "Start for free"
3. **填写信息:**
   - 国家选择: 选择你所在的国家
   - 邮箱: 使用真实邮箱
   - 密码: 设置强密码

4. **验证信用卡** (不会扣费，仅验证身份)
   - ⚠️ **重要:** 这是身份验证，不会收费
   - 💡 **提示:** 可以使用虚拟信用卡

5. **等待账户激活** (通常几分钟到几小时)

---

## 🖥️ **第2步: 创建VM实例**

### 登录控制台
1. 访问: https://cloud.oracle.com/
2. 登录你的账户
3. 点击 "Compute" > "Instances"

### 创建实例
1. **点击 "Create Instance"**

2. **基本配置:**
   ```
   Name: trading-bot
   Availability Domain: (保持默认)
   ```

3. **镜像和形状:**
   ```
   Image: Ubuntu 20.04 (推荐)
   Shape: VM.Standard.E2.1.Micro (Always Free)
   ```

4. **网络配置:**
   ```
   VCN: (保持默认)
   Subnet: (保持默认)
   Public IP: Assign a public IPv4 address ✅
   ```

5. **SSH密钥:**
   - 选择 "Generate SSH key pair"
   - **下载私钥文件** (很重要！)
   - 保存到安全位置

6. **点击 "Create"**

---

## 🔧 **第3步: 连接到服务器**

### macOS/Linux连接:
```bash
# 修改私钥权限
chmod 600 ~/Downloads/ssh-key-*.key

# 连接服务器 (替换IP地址)
ssh -i ~/Downloads/ssh-key-*.key ubuntu@YOUR_PUBLIC_IP
```

### 首次连接配置:
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和pip
sudo apt install python3 python3-pip git -y

# 安装conda (推荐)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b
echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 重新连接或运行: source ~/.bashrc
```

---

## 📥 **第4步: 部署交易系统**

### 克隆代码 (选择一种方式):

**方式1: 如果你有GitHub仓库**
```bash
git clone https://github.com/your-username/your-repo.git trading_bot
cd trading_bot
```

**方式2: 手动上传代码**
```bash
# 在本地打包代码
tar -czf trading_bot.tar.gz --exclude='.git' --exclude='__pycache__' --exclude='logs' *

# 上传到服务器 (新终端窗口)
scp -i ~/Downloads/ssh-key-*.key trading_bot.tar.gz ubuntu@YOUR_PUBLIC_IP:~/

# 在服务器解压
tar -xzf trading_bot.tar.gz
mkdir trading_bot && tar -xzf trading_bot.tar.gz -C trading_bot
cd trading_bot
```

### 配置环境:
```bash
# 创建conda环境
conda create -n eod_options_trading python=3.9 -y
conda activate eod_options_trading

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp config.env.example .env
nano .env  # 编辑配置文件
```

### 编辑配置文件:
```bash
# 在.env文件中添加你的API密钥
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

---

## 🚀 **第5步: 启动系统**

### 创建启动脚本:
```bash
cat > start_trading.sh << 'EOF'
#!/bin/bash
cd ~/trading_bot
source ~/miniconda3/etc/profile.d/conda.sh
conda activate eod_options_trading
nohup python main.py > trading.log 2>&1 &
echo "Trading bot started. PID: $!"
echo $! > trading_bot.pid
EOF

chmod +x start_trading.sh
```

### 启动交易系统:
```bash
./start_trading.sh
```

### 检查运行状态:
```bash
# 查看实时日志
tail -f trading.log

# 检查进程
ps aux | grep python

# 查看进程ID
cat trading_bot.pid
```

---

## 🔄 **第6步: 配置自动启动**

### 创建systemd服务:
```bash
sudo nano /etc/systemd/system/trading-bot.service
```

### 添加以下内容:
```ini
[Unit]
Description=EOD Options Trading Bot
After=network.target

[Service]
Type=forking
User=ubuntu
WorkingDirectory=/home/ubuntu/trading_bot
Environment=PATH=/home/ubuntu/miniconda3/envs/eod_options_trading/bin:/home/ubuntu/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/home/ubuntu/miniconda3/envs/eod_options_trading/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=file:/home/ubuntu/trading_bot/trading.log
StandardError=file:/home/ubuntu/trading_bot/error.log

[Install]
WantedBy=multi-user.target
```

### 启用自动启动:
```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable trading-bot

# 启动服务
sudo systemctl start trading-bot

# 检查状态
sudo systemctl status trading-bot
```

---

## 📊 **第7步: 监控和管理**

### 常用命令:
```bash
# 查看日志
tail -f ~/trading_bot/trading.log

# 重启服务
sudo systemctl restart trading-bot

# 停止服务
sudo systemctl stop trading-bot

# 查看服务状态
sudo systemctl status trading-bot

# 手动启动 (如果不用systemd)
cd ~/trading_bot && ./start_trading.sh
```

### 设置日志轮转:
```bash
sudo nano /etc/logrotate.d/trading-bot
```

添加内容:
```
/home/ubuntu/trading_bot/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

---

## 🆘 **故障排除**

### 常见问题:

**1. 连接被拒绝**
```bash
# 检查防火墙设置
sudo ufw status
sudo ufw allow ssh
```

**2. Python包安装失败**
```bash
# 更新pip
pip install --upgrade pip

# 逐个安装依赖
pip install alpaca-py loguru rich pandas numpy talib
```

**3. 时区设置**
```bash
# 设置为美东时间
sudo timedatectl set-timezone America/New_York
date  # 验证时间
```

**4. 内存不足**
```bash
# 创建swap文件
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 🔒 **安全配置**

### 基本安全设置:
```bash
# 更改SSH端口 (可选)
sudo nano /etc/ssh/sshd_config
# 找到 #Port 22，改为 Port 2222

# 禁用密码登录
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no

# 重启SSH服务
sudo systemctl restart ssh

# 配置防火墙
sudo ufw enable
sudo ufw allow 2222/tcp  # 如果改了SSH端口
```

---

## 📈 **性能优化**

### 系统优化:
```bash
# 调整系统参数
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'net.core.rmem_default = 262144' | sudo tee -a /etc/sysctl.conf
echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf

# 应用设置
sudo sysctl -p
```

---

## ✅ **部署完成检查清单**

- [ ] Oracle Cloud账户创建成功
- [ ] VM实例运行正常
- [ ] SSH连接成功
- [ ] Python环境配置完成
- [ ] 交易系统代码部署
- [ ] 环境变量配置正确
- [ ] 系统正常启动
- [ ] 日志输出正常
- [ ] 自动启动配置
- [ ] 监控设置完成

🎉 **恭喜！你的交易系统现在在云端24/7运行了！**

---

## 📞 **获取帮助**

如果遇到问题:
1. 检查日志: `tail -f ~/trading_bot/trading.log`
2. 验证配置: 确保API密钥正确
3. 重启服务: `sudo systemctl restart trading-bot`
4. 查看系统状态: `sudo systemctl status trading-bot` 