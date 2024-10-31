from datetime import datetime
import threading
import time
import logging
from ssh_operations import ssh_to_switch
from email_notifications import send_email
from dnac_api import get_ap_info_dynamically

active_timers = {}

# handle_ap_disjoin 改为一个独立线程函数
def handle_ap_disjoin(ap_name, staticcdp, config, event_time, stop_event):
    logger = logging.getLogger('ap_debug')
    try:
        print(f"AP {ap_name} 掉线 ，开始处理...")
        logger.info(f"AP {ap_name} 掉线 ，开始处理...")

        # 初始动态获取 AP 信息
        ap_info = get_ap_info_dynamically(ap_name)

        # 如果动态获取失败，等待 30 秒后再试一次
        if not ap_info:
            print(f"动态获取 AP {ap_name} 的信息失败，等待 30 秒后重试...")
            logger.warning(f"动态获取 AP {ap_name} 的信息失败，等待 30 秒后重试...")
            time.sleep(30)
            ap_info = get_ap_info_dynamically(ap_name)

        # 使用静态 CSV 信息（如动态获取失败）
        if not ap_info and ap_name in staticcdp:
            print(f"动态获取失败，尝试使用 CSV 中的静态信息获取 AP {ap_name} 的信息")
            logger.info(f"动态获取失败，尝试使用 CSV 中的静态信息获取 AP {ap_name} 的信息")
            ap_info = staticcdp[ap_name]

        if not ap_info:
            error_msg = f"未能找到 AP {ap_name} 的相关信息（动态和静态均失败）"
            print(error_msg)
            logger.error(error_msg)
            return

        switch_ip = ap_info['switch_ip']
        connect_port = ap_info['connect_port']

        #  定期检查 stop_event 是否触发
        total_wait = 7 * 60
        check_interval = 10
        elapsed = 0

        print(f"AP {ap_name} 的信息已获取，开始等待")
        logger.info(f"AP {ap_name} 的信息已获取，开始等待")

        while elapsed < total_wait:
            if stop_event.is_set():
                print(f"AP {ap_name} 已恢复，停止修复操作")
                logger.info(f"AP {ap_name} 已恢复，停止修复操作")
                return  # 退出函数
            time.sleep(check_interval)
            elapsed += check_interval

        retry_count = 0
        while retry_count < 3:
            if stop_event.is_set():  # 检查 stop_event 是否触发
                print(f"AP {ap_name} 恢复，停止修复操作")
                logger.info(f"AP {ap_name} 恢复，停止修复操作")
                return  # 退出线程

            print(f"开始第 {retry_count + 1} 次修复尝试")
            logger.info(f"开始第 {retry_count + 1} 次修复尝试")
            if ssh_to_switch(switch_ip, connect_port, config):
                print(f"已在交换机 {switch_ip} 上执行 shut/no shut 操作")
                logger.info(f"已在交换机 {switch_ip} 上执行 shut/no shut 操作")

                # 将等待时间分成更短的间隔来检查 stop_event
                total_wait = 7 * 60
                check_interval = 10
                elapsed = 0

                while elapsed < total_wait:
                    if stop_event.is_set():
                        print(f"AP {ap_name} 恢复，停止修复操作")
                        logger.info(f"AP {ap_name} 恢复，停止修复操作")
                        return  # 退出线程
                    time.sleep(check_interval)
                    elapsed += check_interval

                retry_count += 1  # 完成等待后增加重试次数
            else:
                retry_count += 1
                print(f"修复尝试 {retry_count} 失败，等待后重试")
                logger.warning(f"修复尝试 {retry_count} 失败，等待后重试")


        print(f"AP {ap_name} 未恢复，发送邮件通知")
        logger.info(f"AP {ap_name} 未恢复，发送邮件通知")
        send_email(ap_name, ap_info['switch_name'], switch_ip, connect_port, event_time, config)

    except Exception as e:
        logger.error(f"处理 AP {ap_name} 掉线时发生异常: {e}")

# 调用 handle_ap_disjoin_log 时创建线程和事件
def handle_ap_disjoin_log(ap_name, staticcdp, config):
    logger = logging.getLogger('ap_debug')
    if ap_name not in active_timers:
        #print(f"AP {ap_name} 掉线")
        #logger.info(f"AP {ap_name} 掉线")
        event_time = datetime.now()

        # 创建 stop_event 用于控制线程的停止
        stop_event = threading.Event()
        timer_thread = threading.Thread(target=handle_ap_disjoin, args=(ap_name, staticcdp, config, event_time, stop_event))

        # 存储线程和事件到 active_timers 中
        active_timers[ap_name] = {'thread': timer_thread, 'event': stop_event}
        timer_thread.start()
    else:
        print(f"AP {ap_name} 的掉线计时器已存在")
        logger.warning(f"AP {ap_name} 的掉线计时器已存在")

# 在 handle_ap_join_log 中取消计时器并触发事件
def handle_ap_join_log(ap_name):
    logger = logging.getLogger('ap_debug')
    try:
        if ap_name in active_timers:
            active_timers[ap_name]['event'].set()  # 触发事件以终止线程
            active_timers[ap_name]['thread'].join()  # 确保线程终止
            print(f"AP {ap_name} 恢复，取消掉线计时器")
            logger.info(f"AP {ap_name} 恢复，取消掉线计时器")
            del active_timers[ap_name]  # 从 active_timers 中删除 AP
    except Exception as e:
        logger.error(f"取消掉线计时器时发生异常: {e}")
