import yaml
import logging
import socket

# 读取配置文件
def load_config():
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    return config

class UDPSyslogHandler(logging.Handler):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def emit(self, record):
        try:
            msg = self.format(record)
            #print(f"准备发送消息到 {self.host}:{self.port} -> {msg}")  # 发送前调试信息
            sent_bytes = self.sock.sendto(msg.encode('utf-8'), (self.host, self.port))
            #print(f"已发送 {sent_bytes} 字节到 {self.host}:{self.port}")  # 发送后调试信息
        except Exception as e:
            print(f"发送 syslog 消息失败: {e}")


def setup_logging(config):
    logger = logging.getLogger('ap_debug')
    logger.setLevel(logging.DEBUG)

    syslog_server = config['syslog']['server']
    syslog_port = config['syslog']['port']

    # 初始化 syslog 处理器
    syslog_handler = UDPSyslogHandler(syslog_server, syslog_port)
    syslog_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    syslog_handler.setFormatter(formatter)
    logger.addHandler(syslog_handler)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 确认处理器已添加
    logger.info("日志系统已初始化，syslog 处理器已添加")

    return logger





# 从CSV加载AP信息
def load_ap_info(filename):
    ap_info = {}
    try:
        with open(filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ap_info[row['ap_name']] = {
                    'switch_name': row['switch_name'],
                    'switch_ip': row['switch_ip'],
                    'connect_port': row['connect_port']
                }
        print(f"成功加载AP信息，共 {len(ap_info)} 条记录")
    except Exception as e:
        logger = logging.getLogger('ap_debug')
        logger.error(f"加载AP信息时出现错误: {e}")
    return ap_info
