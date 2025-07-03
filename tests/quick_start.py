#!/usr/bin/env python3
"""
EOD期权交易系统 - 快速启动脚本
帮助用户快速配置和启动系统
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                EOD期权交易系统 - 快速启动                ║
║                                                          ║
║        🚀 SPY当日到期期权自动交易系统                    ║
║        ⚠️  高风险投资，请谨慎使用                        ║
╚══════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要Python 3.8+")
        print(f"   当前版本: {sys.version}")
        return False
    
    print(f"✅ Python版本检查通过: {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_dependencies():
    """检查依赖库"""
    print("\n📦 检查依赖库...")
    
    required_packages = [
        'pandas', 'numpy', 'yfinance', 'loguru', 
        'pydantic', 'rich', 'streamlit', 'plotly',
        'requests', 'schedule'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ 缺少依赖库: {', '.join(missing_packages)}")
        install = input("是否自动安装缺少的依赖？(y/n): ").lower().strip()
        
        if install == 'y':
            print("正在安装依赖...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    "-r", "requirements.txt"
                ])
                print("✅ 依赖安装完成")
                return True
            except subprocess.CalledProcessError:
                print("❌ 依赖安装失败，请手动安装")
                return False
        else:
            return False
    
    return True

def setup_configuration():
    """设置配置文件"""
    print("\n⚙️ 配置设置...")
    
    env_file = Path(".env")
    env_example = Path("config.env.example")
    
    if env_file.exists():
        print("✅ 配置文件已存在")
        update = input("是否重新配置？(y/n): ").lower().strip()
        if update != 'y':
            return True
    
    if not env_example.exists():
        print("❌ 配置模板文件不存在")
        return False
    
    print("\n📝 请输入配置信息:")
    print("💡 如果您还没有Alpaca账户，请访问: https://alpaca.markets")
    
    # 获取用户输入
    api_key = input("🔑 Alpaca API Key: ").strip()
    secret_key = input("🔒 Alpaca Secret Key: ").strip()
    
    if not api_key or not secret_key:
        print("❌ API密钥不能为空")
        return False
    
    # 选择环境
    print("\n🌍 选择交易环境:")
    print("1. 纸面交易 (推荐，无风险)")
    print("2. 实盘交易 (高风险)")
    
    env_choice = input("请选择 (1/2): ").strip()
    
    if env_choice == "1":
        base_url = "https://paper-api.alpaca.markets"
        print("✅ 选择纸面交易环境")
    elif env_choice == "2":
        base_url = "https://api.alpaca.markets"
        print("⚠️ 选择实盘交易环境 - 请谨慎操作")
        confirm = input("确认使用实盘环境？(yes/no): ").lower().strip()
        if confirm != "yes":
            print("已取消")
            return False
    else:
        print("❌ 无效选择")
        return False
    
    # 其他配置
    print("🔧 配置交易参数...")
    
    # 风险管理参数
    max_daily_risk = input("📈 每日最大风险比例 (默认2.0%): ").strip()
    if not max_daily_risk:
        max_daily_risk = "2.0"
    
    max_single_risk = input("🎯 单笔最大风险比例 (默认1.0%): ").strip()
    if not max_single_risk:
        max_single_risk = "1.0"
    
    max_trades = input("🔢 每日最大交易次数 (默认5): ").strip()
    if not max_trades:
        max_trades = "5"
    
    # 生成配置文件
    config_content = f"""# Alpaca API配置
ALPACA_API_KEY={api_key}
ALPACA_SECRET_KEY={secret_key}
ALPACA_BASE_URL={base_url}

# 风险管理配置 - 账户资金从API自动获取
MAX_DAILY_RISK_PCT={max_daily_risk}
MAX_SINGLE_TRADE_RISK_PCT={max_single_risk}
MAX_DAILY_TRADES={max_trades}

# 策略参数
SYMBOL=SPY
ORB_PERIOD_MINUTES=15
VWAP_DEVIATION_PCT=0.2
STOP_LOSS_PCT=10.0
TAKE_PROFIT_PCT=20.0

# 时间配置
TRADING_START_TIME=09:30
TRADING_END_TIME=15:50
FORCE_CLOSE_TIME=15:45

# 通知配置（可选）
SLACK_WEBHOOK_URL=
EMAIL_SMTP_SERVER=
EMAIL_USERNAME=
EMAIL_PASSWORD=
"""
    
    with open(env_file, 'w') as f:
        f.write(config_content)
    
    print("✅ 配置文件创建成功")
    return True

def run_system_test():
    """运行系统测试"""
    print("\n🧪 运行系统测试...")
    
    test_choice = input("是否运行系统测试？(y/n): ").lower().strip()
    if test_choice != 'y':
        return True
    
    try:
        result = subprocess.run([sys.executable, "test_system.py"], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        return False

def show_startup_options():
    """显示启动选项"""
    print("\n🚀 系统启动选项:")
    print("1. 启动交易机器人 (终端模式)")
    print("2. 启动Web监控界面")
    print("3. 运行系统测试")
    print("4. 查看帮助文档")
    print("5. 退出")
    
    choice = input("\n请选择操作 (1-5): ").strip()
    
    if choice == "1":
        print("\n启动交易机器人...")
        print("💡 使用 Ctrl+C 停止机器人")
        try:
            subprocess.run([sys.executable, "main.py", "--mode", "test"])
        except KeyboardInterrupt:
            print("\n机器人已停止")
    
    elif choice == "2":
        print("\n启动Web监控界面...")
        print("💡 浏览器将自动打开 http://localhost:8501")
        try:
            subprocess.run([sys.executable, "-m", "streamlit", "run", "web_dashboard.py"])
        except KeyboardInterrupt:
            print("\n监控界面已停止")
    
    elif choice == "3":
        subprocess.run([sys.executable, "test_system.py"])
    
    elif choice == "4":
        print("\n📖 帮助文档:")
        print("- README.md: 完整的项目文档")
        print("- config.env.example: 配置文件示例")
        print("- 在线文档: 查看项目仓库")
    
    elif choice == "5":
        print("👋 再见!")
        return False
    
    else:
        print("❌ 无效选择")
    
    return True

def main():
    """主函数"""
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败，请手动安装依赖后重试")
        sys.exit(1)
    
    # 设置配置
    if not setup_configuration():
        print("❌ 配置设置失败")
        sys.exit(1)
    
    # 运行测试
    if not run_system_test():
        print("⚠️ 系统测试未通过，但您仍可以继续")
    
    # 启动选项循环
    while True:
        try:
            if not show_startup_options():
                break
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，退出程序")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            break

if __name__ == "__main__":
    main() 