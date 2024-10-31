import yaml
import logging
from csv_operations import load_ap_info_csv
from syslog_listener import start_syslog_listener
from dnac_api import get_ap_info_dynamically
from config import setup_logging

def main():
    # 显式设置根记录器的日志级别为 DEBUG
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('ap_debug')
    logger.setLevel(logging.DEBUG)

    # 读取配置文件
    try:
        with open('config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
    except Exception as e:
        print(f"无法加载配置文件: {e}")
        logger.error(f"无法加载配置文件: {e}")
        exit(1)

    # 设置日志（使用配置文件）
    logger = setup_logging(config)  # 重新设置 logger，确保它包含 UDPSyslogHandler

    # 导入 CSV 数据，保存为 staticcdp 字典
    try:
        staticcdp = load_ap_info_csv('cdpnei_ap.csv')  # 假设 CSV 文件为 cdpnei_ap.csv
    except Exception as e:
        print(f"无法加载 CSV 文件: {e}")
        logger.error(f"无法加载 CSV 文件: {e}")
        exit(1)

    print("开始监听TCP 2333端口的 syslog...")
    logger.info("开始监听TCP 2333端口的 syslog...")

    # 检查附加的处理器
    print("当前附加的日志处理器:", logger.handlers)
    logger.info("检查附加的日志处理器...")

    # 启动 syslog 监听器
    start_syslog_listener(staticcdp, config)

if __name__ == "__main__":
    main()
