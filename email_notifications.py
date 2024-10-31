import paramiko
import logging
import time
from email.mime.text import MIMEText
import smtplib
from datetime import datetime


def port_diag(switch_ip, connect_port, config):
    logger = logging.getLogger('ap_debug')
    username = config['credentials']['username']
    password = config['credentials']['password']
    output = ""

    try:
        logger.info(f"正在连接交换机 {switch_ip} 进行诊断")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 强制使用用户名和密码
        ssh.connect(switch_ip, port=22, username=username, password=password, look_for_keys=False, allow_agent=False)

        # 打开交互式 shell
        shell = ssh.invoke_shell()

        # 定义需要执行的命令列表
        commands = [
            f"show run interface {connect_port}",
            f"show power inline {connect_port}",
            f"show interface {connect_port}"
        ]

        for command in commands:
            shell.send(command + "\n")
            time.sleep(1)  # 等待命令开始执行

            # 循环检查输出并处理分页
            while True:
                chunk = shell.recv(65535).decode('utf-8')
                output += chunk
                # 检查是否有分页提示
                if "--More--" in chunk:
                    shell.send(" ")  # 发送空格键继续输出
                    time.sleep(0.5)  # 小等待避免过快发送
                else:
                    break  # 如果没有分页提示，退出循环

            time.sleep(1)  # 确保命令完全执行完毕

        ssh.close()
        logger.info(f"诊断完成，获取到的输出: {output}")

    except Exception as e:
        logger.error(f"诊断过程中出现错误: {e}")
        output = f"诊断过程中出现错误: {e}"

    return output



def send_email(ap_name, switch_name, switch_ip, connect_port, event_time, config):
    try:
        logger = logging.getLogger('ap_debug')
        current_time = datetime.now()
        time_diff = current_time - event_time
        time_diff_str = str(time_diff).split('.')[0]

        smtp_server = config['email']['smtp_server']
        smtp_port = config['email']['smtp_port']
        sender = config['email']['sender']
        recipients = config['email']['recipients']

        subject = f"{switch_name}上{connect_port}连接的{ap_name}离线，当前时间 {current_time.strftime('%Y-%m-%d %H:%M:%S')}"

        # 调用 port_diag 获取诊断输出
        diag_output = port_diag(switch_ip=switch_ip, connect_port=connect_port, config=config)

        body = (f"{ap_name}离线，连接交换机为{switch_name}，端口为{connect_port}，"
                f"已重置端口三次，未能恢复，距离掉线已有 {time_diff_str}\n\n"
                f"端口诊断信息:\n{diag_output}")

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.sendmail(sender, recipients, msg.as_string())

        logger.info(f"邮件发送成功，发送至 {', '.join(recipients)}")
    except Exception as e:
        logger.error(f"发送邮件失败: {e}")

