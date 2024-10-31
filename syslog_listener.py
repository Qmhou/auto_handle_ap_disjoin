import socket
import logging
from ap_operations import handle_ap_disjoin_log, handle_ap_join_log
from utils import parse_syslog_message

def start_syslog_listener(staticcdp, config):
    try:
        logger = logging.getLogger('ap_debug')
        print("启动 syslog 监听...")
        logger.info("启动 syslog 监听...")

        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind(('0.0.0.0', 2333))

        while True:
            try:
                message, _ = server.recvfrom(1024)
                message = message.decode('utf-8')

                # 解析 syslog 消息以获取 AP 名称和事件类型
                ap_name, event_type = parse_syslog_message(message)

                if ap_name:
                    # 根据事件类型执行相应操作
                    if event_type == 'disjoin':
                        handle_ap_disjoin_log(ap_name, staticcdp, config)
                    elif event_type == 'join':
                        handle_ap_join_log(ap_name)
                #else:
                    #logger.warning("解析 syslog 消息时未能找到 AP 名称")

            except Exception as e:
                logger.error(f"在处理 syslog 消息时出现异常: {e}")
                print(f"在处理 syslog 消息时出现异常: {e}")

    except Exception as e:
        logger.critical(f"启动 syslog 监听时发生严重错误: {e}")
        print(f"启动 syslog 监听时发生严重错误: {e}")
