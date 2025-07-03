# 📱 MacBook关盖运行指南

## 🤔 问题
默认情况下，关闭MacBook Pro的盖子会让系统进入睡眠模式，暂停所有正在运行的程序。

## 💡 解决方案

我已经为你创建了几种运行方式，选择最适合你的：

---

## 🚀 **方案1: 防睡眠运行 (推荐新手)**

```bash
./run_trading_bot_keep_awake.sh
```

**特点:**
- ✅ 最简单，一键启动
- ✅ 自动防止Mac睡眠
- ✅ 关盖后继续运行
- ❌ 关闭终端会停止程序

**使用场景:** 短期运行，不关闭终端

---

## 🖥️ **方案2: Screen会话 (推荐高级用户)**

```bash
./run_trading_bot_screen.sh
```

**启动后管理:**
```bash
screen -r trading_bot    # 重新连接会话
# 按 Ctrl+A, D 分离会话
# 按 Ctrl+C 停止程序
```

**特点:**
- ✅ 可以关闭终端
- ✅ 可以远程重新连接
- ✅ 会话持久化
- ⚡ 需要学习Screen命令

**使用场景:** 长期运行，需要远程管理

---

## 🔄 **方案3: 后台运行 (推荐无人值守)**

```bash
./run_trading_bot_nohup.sh
```

**查看状态:**
```bash
tail -f trading_bot.log    # 查看实时日志
```

**特点:**
- ✅ 完全后台运行
- ✅ 可以关闭终端
- ✅ 自动保存日志
- ✅ 最稳定的方式

**使用场景:** 长期无人值守运行

---

## 🛠️ **管理命令**

### 检查状态
```bash
./check_trading_bot_status.sh
```

### 停止程序
```bash
./stop_trading_bot.sh
```

---

## 📋 **完整操作流程**

### 第一次使用 (推荐)
1. **启动程序:**
   ```bash
   ./run_trading_bot_nohup.sh
   ```

2. **检查状态:**
   ```bash
   ./check_trading_bot_status.sh
   ```

3. **关闭MacBook盖子** - 程序继续运行 ✅

4. **重新打开后查看日志:**
   ```bash
   tail -f trading_bot.log
   ```

5. **停止程序:**
   ```bash
   ./stop_trading_bot.sh
   ```

---

## ⚠️ **注意事项**

1. **电源管理:** 确保MacBook连接电源，避免电池耗尽
2. **网络连接:** 确保WiFi连接稳定
3. **系统更新:** 避免在交易时间自动更新系统
4. **监控日志:** 定期检查日志确保程序正常运行

---

## 🆘 **故障排除**

### 如果程序无响应:
```bash
./stop_trading_bot.sh      # 强制停止
./check_trading_bot_status.sh  # 检查状态
```

### 如果找不到进程:
```bash
ps aux | grep python       # 手动查找进程
kill -9 [进程ID]           # 强制终止
```

### 如果Screen会话丢失:
```bash
screen -ls                 # 列出所有会话
screen -r trading_bot      # 重新连接
```

---

## 📞 **推荐设置**

**日常交易使用:**
```bash
./run_trading_bot_nohup.sh  # 启动
# 关闭MacBook盖子
# 正常使用其他设备
```

**临时测试使用:**
```bash
./run_trading_bot_keep_awake.sh  # 简单启动测试
```

🎯 **现在你可以安心关闭MacBook盖子，交易系统会继续运行！** 